import base64
import time
import requests
import json
import re
from difflib import SequenceMatcher
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

FOLDER_ID = "b1gjtfjpbhsk7d6qjfnj"
OUTFILE = "transcription.txt"
STT_BASE = "https://stt.api.cloud.yandex.net/stt/v3"
HEADERS = {
    "Authorization": f"Api-Key {API_KEY}",
    "x-folder-id": FOLDER_ID,
    "Content-Type": "application/json",
}

_NUM_WORDS = (
    "ноль|один|одна|одно|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять|"
    "одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|"
    "семнадцать|восемнадцать|девятнадцать|двадцать|тридцать|сорок|пятьдесят|"
    "шестьдесят|семьдесят|восемьдесят|девяносто|сто|полтора"
)
RE_TIME = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")
RE_NUM = re.compile(r"\b\d+([.,]\d+)?\b")
RE_NUMW = re.compile(rf"\b({_NUM_WORDS})\b", re.IGNORECASE)
RE_PUN = re.compile(r"[^\w\s]+", re.UNICODE)

def normalize_for_dedupe(text: str) -> str:
    t = text.lower()
    t = RE_TIME.sub(" num ", t)
    t = RE_NUM.sub(" num ", t)
    t = RE_NUMW.sub(" num ", t)
    t = RE_PUN.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def very_similar(a: str, b: str, thr: float = 0.88) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= thr

def download_mp3_to_base64(url: str) -> str:
    print(f"Скачиваю аудио из {url} ...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    print(f"Размер скачанного файла: {len(r.content)} байт")
    return base64.b64encode(r.content).decode("ascii")

def start_recognition(audio_b64: str) -> str:
    body = {
        "content": audio_b64,
        "recognitionModel": {
            "model": "general",
            "audioFormat": {"containerAudio": {"containerAudioType": "MP3"}},
            "textNormalization": {"textNormalization": "TEXT_NORMALIZATION_ENABLED"}
        }
    }
    r = requests.post(f"{STT_BASE}/recognizeFileAsync", headers=HEADERS, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Unexpected response from recognizeFileAsync: {data}")
    return data["id"]

def wait_for_result(operation_id: str, interval: int = 2, max_wait: int = 3600):
    url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
    waited = 0
    while True:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("done", False):
            return
        #print("Ожидание результата...")
        time.sleep(interval)
        waited += interval
        if waited >= max_wait:
            raise TimeoutError("Превышено время ожидания результата распознавания")

def get_recognition_result(operation_id: str):
    url = f"{STT_BASE}/getRecognition"
    params = {"operationId": operation_id}
    r = requests.get(url, headers=HEADERS, params=params, timeout=60)
    r.raise_for_status()
    results = []
    for line in r.text.strip().splitlines():
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return results

def extract_full_text_dedup(events: list) -> str:
    out_lines: list[str] = []
    norms: list[str] = []

    for item in events:
        res = item.get("result") or {}
        for key in ("finalRefinement", "final"):
            node = res.get(key)
            if not node:
                continue

            txt = None
            try:
                txt = node["normalizedText"]["alternatives"][0]["text"]
            except Exception:
                pass
            if not txt:
                try:
                    txt = node["alternatives"][0]["text"]
                except Exception:
                    pass
            if not txt:
                continue

            txt = txt.strip()
            if not txt:
                continue

            n = normalize_for_dedupe(txt)

            replaced = False
            for i in range(max(0, len(out_lines) - 3), len(out_lines)):
                if n == norms[i] or very_similar(n, norms[i]):
                    if key == "finalRefinement" or len(txt) > len(out_lines[i]):
                        out_lines[i] = txt
                        norms[i] = n
                    replaced = True
                    break

            if not replaced:
                out_lines.append(txt)
                norms.append(n)

    return "\n".join(out_lines)


def recognize_audio_url(req):
    #print("Запускаю распознавание...")
    audio_b64 = download_mp3_to_base64(req['mp3_url'])
    operation_id = start_recognition(audio_b64)
    print(f"ID операции: {operation_id}")
    wait_for_result(operation_id)
    events = get_recognition_result(operation_id)
    text = extract_full_text_dedup(events)
    if text.strip():
        #print("\n===== РАСШИФРОВКА =====\n")
        #print(text)
        #print("\n=======================")
        #with open(OUTFILE, "w", encoding="utf-8") as f:
        #    f.write(text)
        #print(f"💾 Текст сохранён в файл: {OUTFILE}")
        b.call('task.commentitem.add', [req['task_id'], {'POST_MESSAGE': text, 'AUTHOR_ID': '1'}],raw=True)
    else:
        print("Расшифровка пуста.")
    return