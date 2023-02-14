from time import asctime
import os

from flask import request, render_template, redirect, url_for
from flask_login import login_user, login_required, current_user

from web_app_4dk import app
from web_app_4dk import login_manager
from web_app_4dk.models import UserAuth
from web_app_4dk.modules.ServiceTask import create_service_tasks, create_service_tasks_report
from web_app_4dk.modules.UpdateCompanyValue import update_company_value
from web_app_4dk.modules.UpdateCode1C import update_code_1c
from web_app_4dk.modules.UpdateCallStatistic import update_call_statistic
from web_app_4dk.modules.CheckTaskResult import check_task_result
from web_app_4dk.modules.ReviseITS import revise_its
from web_app_4dk.modules.Prolongation_ITS import prolongation_its
from web_app_4dk.modules.CreateDeal import create_deal
from web_app_4dk.modules.Connect1C import connect_1c
from web_app_4dk.modules.UpdateUserStatistics import update_user_statistics
from web_app_4dk.modules.UpdateContactPhoto import update_contact_photo
from web_app_4dk.modules.RewriteCallStatistic import rewrite_call_statistic
from web_app_4dk.modules.CreateDealsRpd import create_deals_rpd
from web_app_4dk.modules.CreateCompanyCallReport import create_company_call_report
from web_app_4dk.modules.ReviseAccountingDeals import revise_accounting_deals
from web_app_4dk.modules.FillContract import fill_contract
from web_app_4dk.modules.CreateLineConsultationReport import create_line_consultation_report
from web_app_4dk.modules.ReviseNewSub import revise_new_sub
from web_app_4dk.modules.CreateRpdReport import create_rpd_report
from web_app_4dk.modules.CreateCompaniesActivityReport import create_companies_activity_report
from web_app_4dk.modules.MegafonCallsHandler import megafon_calls_handler
from web_app_4dk.modules.CreateInfoSmartProcess import create_info_smart_process
from web_app_4dk.modules.SeminarDataHandler import seminar_data_handler
from web_app_4dk.modules.FNSTaskComplete import fns_task_complete
from web_app_4dk.modules.CreateVacation import create_vacation
from web_app_4dk.modules.ChangeResponsible import change_responsible
from web_app_4dk.modules.CompleteDocumentFlowTask import complete_document_flow_task
from web_app_4dk.modules.CreateTaskWithChecklist import create_task_with_checklist
from web_app_4dk.modules.EdoInfoHandler import edo_info_handler
from web_app_4dk.modules.AutoFailure import auto_failure
from web_app_4dk.modules.CreateCurrentMonthDealsDataFile import create_current_month_deals_data_file
from web_app_4dk.modules.CreateServiceSalesReport import create_service_sales_report
from web_app_4dk.modules.AddTaskCommentary import add_task_commentary
from web_app_4dk.modules.CreateServicesCoverageReport import create_services_coverage_report
from web_app_4dk.modules.AddInvoiceToList import add_invoice_to_list
from web_app_4dk.modules.ChangeTaskCreatedBy import change_task_created_by
from web_app_4dk.modules.CompleteCallActivity import complete_call_activity
from web_app_4dk.modules.CreateRecruitmentRequest import create_recruitment_request
from web_app_4dk.modules.CreateTasksActiveSales import create_tasks_active_sales
from web_app_4dk.modules.New1cConnect import connect_1c_event_handler


# Словарь функций для вызова из кастомного запроса

custom_webhooks = {
    'create_task_service': create_service_tasks,
    'create_service_tasks_report': create_service_tasks_report,
    'check_task_result': check_task_result,
    'revise_its': revise_its,
    'prolongation_its': prolongation_its,
    'create_deals_rpd': create_deals_rpd,
    'create_company_call_report': create_company_call_report,
    'fill_contract': fill_contract,
    'create_line_consultation_report': create_line_consultation_report,
    'create_rpd_report': create_rpd_report,
    'create_companies_activity_report': create_companies_activity_report,
    'create_info_smart_process': create_info_smart_process,
    'fns_task_complete': fns_task_complete,
    'complete_document_flow_task': complete_document_flow_task,
    'create_task_with_checklist': create_task_with_checklist,
    'auto_failure': auto_failure,
    'create_service_sales_report': create_service_sales_report,
    'add_task_commentary': add_task_commentary,
    'create_services_coverage_report': create_services_coverage_report,
    'add_invoice_to_list': add_invoice_to_list,
    'change_task_created_by': change_task_created_by,
    'create_recruitment_request': create_recruitment_request,
    'create_tasks_active_sales': create_tasks_active_sales,
}

# Словарь функций для вызова из запроса со стандартным методом

default_webhooks = {
    'ONCRMDEALUPDATE': update_code_1c,
    'ONCRMDEALDELETE': update_company_value,
    'ONVOXIMPLANTCALLEND': update_call_statistic,
    'ONCRMDEALADD': create_deal,
    'ONCRMACTIVITYADD': complete_call_activity,
    'ONTASKADD': update_user_statistics,
    'ONTASKUPDATE': update_user_statistics,
    'ONCRMCONTACTUPDATE': update_contact_photo,
}


# Обработчик стандартных вебхуков Битрикс
@app.route('/bitrix/default_webhook', methods=['POST', 'HEAD'])
def default_webhook():
    update_logs("Получен дефолтный вебхук", request.form)
    default_webhooks[request.form['event']](request.form)
    return 'OK'


# Обработчик кастомных вебхуков Битрикс
@app.route('/bitrix/custom_webhook', methods=['POST', 'HEAD'])
def custom_webhook():
    update_logs("Получен кастомный вебхук", request.args)
    job = request.args['job']
    custom_webhooks[job](request.args)
    return 'OK'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        user = UserAuth.query.filter_by(login=login).first()
        if user:
            if user.password == password:
                login_user(user)
                return redirect(url_for('main_page'))

    return render_template('login.html')


@app.route('/create_current_month_deals_data_file', methods=['GET'])
def create_current_month_deals_data_file_route():
    create_current_month_deals_data_file()
    return 'OK'


@app.route('/update_service_sales_report', methods=['GET'])
def update_service_sales_report():
    create_service_sales_report({'update': True, 'with_current_month': 'N'})
    return 'OK'


@app.route('/send_request_create_service_coverage_report', methods=['GET'])
def send_service_coverage_report_to_employees():
    create_services_coverage_report({'to_all_employees': True})
    return 'OK'



@login_required
@app.route('/', methods=['GET', 'POST'])
def main_page():
    if current_user != 1:
        return redirect(url_for('login'))
    if request.method == 'POST' and request.form.get('submit_button'):
        if request.files['new_call_statistic_file']:
            new_call_statistic_file = request.files['new_call_statistic_file']
            new_call_statistic_file.save('/root/web_app_4dk/web_app_4dk/new_call_statistic.xlsx')
            month = request.form.get('rewrite_calls_month')
            year = request.form.get('rewrite_calls_year')
            rewrite_call_statistic(month, year)
            os.remove('/root/web_app_4dk/web_app_4dk/new_call_statistic.xlsx')
        elif request.files['revise_accounting_deals_file']:
            revise_accounting_deals_file = request.files['revise_accounting_deals_file']
            revise_accounting_deals_file.save('/root/web_app_4dk/web_app_4dk/revise_accounting_deals_file.xlsx')
            revise_accounting_deals('/root/web_app_4dk/web_app_4dk/revise_accounting_deals_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/revise_accounting_deals_file.xlsx')
        elif request.files['newsub_file']:
            newsub_file = request.files['newsub_file']
            newsub_file.save('/root/web_app_4dk/web_app_4dk/newsub_file.xlsx')
            revise_new_sub('/root/web_app_4dk/web_app_4dk/newsub_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/newsub_file.xlsx')
        elif request.files['megafon_file']:
            newsub_file = request.files['megafon_file']
            newsub_file.save('/root/web_app_4dk/web_app_4dk/megafon_file.xlsx')
            megafon_calls_handler('/root/web_app_4dk/web_app_4dk/megafon_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/megafon_file.xlsx')
        elif request.files['registrants_file'] and request.files['questionnaire_file'] and request.form.get('event_id'):
            registrants_file = request.files['registrants_file']
            questionnaire_file = request.files['questionnaire_file']
            event_id = request.form.get('event_id')
            registrants_file.save('/root/web_app_4dk/web_app_4dk/seminar_registrants.xlsx')
            questionnaire_file.save('/root/web_app_4dk/web_app_4dk/seminar_questionnaire.xlsx')
            seminar_data_handler(event_id, '/root/web_app_4dk/web_app_4dk/seminar_registrants.xlsx', '/root/web_app_4dk/web_app_4dk/seminar_questionnaire.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/seminar_registrants.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/seminar_questionnaire.xlsx')
        elif request.files['vacation_file']:
            vacation_file = request.files['vacation_file']
            vacation_file.save('/root/web_app_4dk/web_app_4dk/vacation_file.xlsx')
            create_vacation('/root/web_app_4dk/web_app_4dk/vacation_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/vacation_file.xlsx')
        elif request.files['change_responsible_file'] and request.form.get('new_responsible'):
            new_responsible = request.form.get('new_responsible')
            change_responsible_file = request.files['change_responsible_file']
            change_responsible_file.save('/root/web_app_4dk/web_app_4dk/change_responsible_file.xlsx')
            change_responsible(new_responsible, '/root/web_app_4dk/web_app_4dk/change_responsible_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/change_responsible_file.xlsx')
        elif request.files['edo_info_handler_file']:
            edo_info_handler_file = request.files['edo_info_handler_file']
            month = request.form.get('month')
            year = request.form.get('year')
            edo_info_handler_file.save('/root/web_app_4dk/web_app_4dk/edo_info_handler_file.xlsx')
            edo_info_handler(month, year, '/root/web_app_4dk/web_app_4dk/edo_info_handler_file.xlsx')
            os.remove('/root/web_app_4dk/web_app_4dk/edo_info_handler_file.xlsx')

    return render_template('main_page.html', web_app_logs=read_logs())


@login_manager.user_loader
def load_user(user):
    return 1


# Обработчик вебхуков 1С-Коннект
@app.route('/1c-connect', methods=['POST'])
def update_connect_logs():
    connect_1c_event_handler(request.json)

    #update_logs("Получен 1С-Коннект вебхук", request.json)
    #connect_1c(request.json)

    return 'OK'


# Обновление логов веб-приложения
def update_logs(text, req):
    return
    file_path = '/root/web_app_4dk/web_app_4dk/static/logs/logs.txt'
    log_dct = {}
    for key in req:
        log_dct.setdefault(key, req[key])
    with open(file_path, 'a') as log_file:
        log_file.write(f"{asctime()} | {text} | request: {log_dct}\n")
    if os.stat(file_path).st_size > 10000000:
        with open(file_path, 'w') as file:
            file.write('')


# Вывод на экран логов веб-приложения
def read_logs():
    return [['Логирование отключено']]
    final_text = []
    with open('/root/web_app_4dk/web_app_4dk/static/logs/logs.txt', 'r') as log_file:
        logs = log_file.readlines()
        for s in logs:
            info_text = s.split('request: ')[0]
            request_text = s.split('request: ')[1]
            request_text = request_text.split(',')
            final_text.append([info_text, request_text])
        return final_text[::-1]