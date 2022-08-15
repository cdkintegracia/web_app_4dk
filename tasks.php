<?php
file_put_contents('log.txt', print_r($_REQUEST, true), FILE_APPEND);
//file_put_contents('reestrlog.txt', print_r("111111".$_REQUEST, true), FILE_APPEND);
function query($method, $queryData){
    $rest = 'https://vc4dk.bitrix24.ru/rest/1/lndpuntjuv8j38vv/';
    $queryUrl = $rest.$method;
    $curl = curl_init();
    curl_setopt_array($curl, array(
    CURLOPT_SSL_VERIFYPEER => 0,
    CURLOPT_POST => 1,
    CURLOPT_HEADER => 0,
    CURLOPT_RETURNTRANSFER => 1,
    CURLOPT_URL => $queryUrl,
    CURLOPT_POSTFIELDS => $queryData,
    ));

    $result2 = curl_exec($curl);
    curl_close($curl);

    $result2 = json_decode($result2, 1);
    return $result2;
}


$event = $_REQUEST['event'];
$task = $_REQUEST['data']['FIELDS_AFTER']['ID'];
$queryData = http_build_query(array(
    'filter' => ["ID" => $task],
    'select' => ['UF_*', '*']
));
$tasks = query('tasks.task.list', $queryData);
echo "<pre>";
print_r($tasks);
echo "</pre>";
$result = $tasks['result']['tasks']['0'];
file_put_contents('log.txt', print_r($tasks, true), FILE_APPEND);
$DESCRIPTION = $result['description'];
$title = $result['title'];
$responsibleId = $result['responsibleId'];
$auditors = $result['auditors']['0'];
$title = $result['title'];
if(strpos($title,'ропущенный звонок') > 0 && $event == 'ONTASKADD'){
    $queryData = http_build_query(array(
    "TASKID" => $task,
    'TASKDATA' =>
        [
            "RESPONSIBLE_ID" => $auditors,
			"AUDITORS" => [$responsibleId]
        ],

    ));
	$invoice = query('task.item.update', $queryData);
}

$ufCrmTask = $result['ufCrmTask'];
foreach($ufCrmTask as $key){
    if(strpos($key, 'D_') !== false){$deal = substr($key,2);}
    if(strpos($key, 'C_') !== false){$contact = substr($key,2);}
    if(strpos($key, 'CO_') !== false){$COMPANY_IDs = substr($key,3); $COMPANY_ID = substr($key,3); $company = $key;}
}

echo "<pre>";
print_r($contact);
echo "</pre>";
if($contact){ // && empty($COMPANY_ID)
    $queryData = http_build_query(array(
        'id' => $contact
    ));
    $dtask = query('crm.contact.get', $queryData);
    //print_r($dtask);

    file_put_contents('log.txt', print_r($dtask, true), FILE_APPEND);
    $deal = 'D_'.$deal;
    $contact = 'C_'.$contact;
    if(empty($company)){
        $company = 'CO_'.$dtask['result']['COMPANY_ID'];
        $COMPANY_ID = $dtask['result']['COMPANY_ID'];
        echo "<pre>";
        print_r($company);
        echo "</pre>";
    }
    echo "<pre>";
    print_r($company);
    echo "</pre>";
}

if(!empty($COMPANY_ID)){
    $queryData = http_build_query(array(
        'id' => $COMPANY_ID
    ));
    $dtask = query('crm.company.get', $queryData);
    echo "<pre>";    print_r($dtask);  echo "</pre>";
    echo "<pre>";  print_r('TITLE - '.$TITLE.' title - '.$title.' CTitle - '.$CTitle); echo "</pre>";
    $CTitle = $dtask['result']['TITLE'];
    echo "<pre>";  print_r('TITLE - '.$TITLE.' title - '.$title.' CTitle - '.$CTitle); echo "</pre>";
    $TITLE = $title.' '.$dtask['result']['TITLE'];
    echo "<pre>";  print_r('TITLE - '.$TITLE.' title - '.$title.' CTitle - '.$CTitle); echo "</pre>";
    if(strpos($title,$CTitle) == 0){
        echo "<pre>";  print_r('TITLE - '.$TITLE.' title - '.$title.' CTitle - '.$CTitle); echo "</pre>";

        if($contact){
            $queryData = http_build_query(array(
                "TASKID" => $task,
                'TASKDATA' =>
                    [
                        "TITLE" => $TITLE,
                        'UF_CRM_TASK' => [$contact, $company, $deal]
                    ],
            ));
            $invoice = query('task.item.update', $queryData);
            file_put_contents('log.txt', print_r($invoice, true), FILE_APPEND);
        }

        if(empty($contact)){
            $queryData = http_build_query(array(
            "TASKID" => $task,
            'TASKDATA' =>
                [
                    "TITLE" => $TITLE,
                ],
            ));
        	$invoice = query('task.item.update', $queryData);

        	file_put_contents('log.txt', print_r($invoice, true), FILE_APPEND);
        }
    }
}
//Реестр задач
$taskStatusArr = Array(
    "2"     => 343,
    "-1"    => 345,
    "-3"    => 347,
    "3"     => 349,
    "4"     => 351,
    "5"     => 353,
    "6"     => 355,
    );

$groupsResult = query('sonet_group.get', Array());
$groupArr = Array();
foreach ($groupsResult["result"] as $groupItem){
    $groupArr[$groupItem["ID"]] = $groupItem["NAME"];
}

$queryTagsData = http_build_query(array(
    'TASK_ID' => $task
));
$tagsResponse = query('task.item.gettags', $queryTagsData);
$tags = !empty($tagsResponse["result"]) ? implode(", ", $tagsResponse["result"]) : "" ;


$queryReestrCurrentData = http_build_query(array(
    'IBLOCK_TYPE_ID'    => 'lists',
    'IBLOCK_ID'         => '107',
    'FILTER'            => Array('PROPERTY_517' => $task),
));
$tasksReestrCurrent = query('lists.element.get', $queryReestrCurrentData);
file_put_contents('reestrlog.txt', print_r("lists.element.get", true), FILE_APPEND);
file_put_contents('reestrlog.txt', print_r($tasksReestrCurrent, true), FILE_APPEND);
if(!empty($tasksReestrCurrent["result"])){
    sleep(3);
    $queryTaskReestrUpdateData = http_build_query(array(
        "IBLOCK_TYPE_ID"    => "lists",
        "IBLOCK_ID"         => "107",
        "ELEMENT_CODE"      => $tasksReestrCurrent["result"][0]["CODE"],
        "ELEMENT_ID"        => $tasksReestrCurrent["result"][0]["ID"],
        "LIST_ELEMENT_URL"  => "https://vc4dk.bitrix24.ru/workgroups/group/".$result["groupId"]."/tasks/task/view/".$result["id"]."/",
        "FIELDS"            => Array(
            "NAME"         => $result["title"],
            "PROPERTY_517" => Array(key($tasksReestrCurrent["result"][0]["PROPERTY_517"]) => $result["id"]), // Привязка к задаче
            "PROPERTY_495" => $taskStatusArr[$result["status"]], //Статус
            "PROPERTY_499" => !empty($COMPANY_ID) ? $COMPANY_ID : "" , //Компания
            "PROPERTY_501" => !empty($contact) ? $contact : "", //Контакт
            "PROPERTY_537" => Array(key($tasksReestrCurrent["result"][0]["PROPERTY_537"]) => !empty($result["groupId"]) ? $groupArr[$result["groupId"]] : ""), //Проект
            "PROPERTY_505" => $result["createdDate"], //Дата/время создания
            "PROPERTY_507" => $result["closedDate"], //Дата/время завершения
            "PROPERTY_509" => $result["createdBy"], //Постановщик
            "PROPERTY_511" => $result["responsibleId"], //Ответственный
            "PROPERTY_515" => Array(key($tasksReestrCurrent["result"][0]["PROPERTY_517"]) => $tags), //Теги
            "PROPERTY_513" => $result["durationFact"], //Текущие трудозатраты
            ),
    ));
    $tasksReestrUpdate = query('lists.element.update', $queryTaskReestrUpdateData);
}
elseif($event == 'ONTASKADD') {
    $queryTaskReestrData = http_build_query(array(
        "IBLOCK_TYPE_ID"    => "lists",
        "IBLOCK_ID"         => "107",
        "ELEMENT_CODE"      => "TASK_REESTR_".$result["id"],
        "LIST_ELEMENT_URL"  => "https://vc4dk.bitrix24.ru/workgroups/group/".$result["groupId"]."/tasks/task/view/".$result["id"]."/",
        "FIELDS"            => Array(
            "NAME"         => $result["title"],
            "PROPERTY_517" => $result["id"], // Привязка к задаче
            "PROPERTY_495" => $taskStatusArr[$result["status"]], //Статус
            "PROPERTY_499" => !empty($COMPANY_ID) ? $COMPANY_ID : "" , //Компания
            "PROPERTY_501" => !empty($contact) ? $contact : "", //Контакт
            "PROPERTY_537" => !empty($result["groupId"]) ? $groupArr[$result["groupId"]] : "", //Проект
            "PROPERTY_505" => $result["createdDate"], //Дата/время создания
            "PROPERTY_507" => $result["closedDate"], //Дата/время завершения
            "PROPERTY_509" => $result["createdBy"], //Постановщик
            "PROPERTY_511" => $result["responsibleId"], //Ответственный
            "PROPERTY_515" => $tags, //Теги
            "PROPERTY_513" => $result["durationFact"], //Текущие трудозатраты
            ),
    ));
    $tasksReestr = query('lists.element.add', $queryTaskReestrData);
}