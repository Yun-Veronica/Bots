import json
import requests

YADISK_TOKEN = "y0_AgAAAAA_9BU1AADLWwAAAADpqs7lHKMzOyYHQcu04duyMltGa4mkqdA"
file_path_to_write = "settings.json"
file_path = "https://disk.yandex.ru/d/Ae_MrwDzsHuqQg"


# получение файла с номером телефона
def getting_link_to_download(path=file_path):
    final_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={path}"
    response = requests.get(final_url)
    parse_href = response.json()['href']
    return parse_href


def get_text_from_file():
    to_download_from_link = getting_link_to_download()
    # link=f"https://cloud-api.yandex.net/v1/disk/resources/download/?path={path}"
    file = requests.get(to_download_from_link)
    text = dict(file.json())

    return text


def getting_link_to_upload():
    path = file_path_to_write
    link = f"https://cloud-api.yandex.net/v1/disk/resources/upload"
    response = requests.get(link, headers={"Authorization": f"OAuth {YADISK_TOKEN}", "Content-Type": "application/json"},
                            params={'fields': "href",
                                    "path": f"{path}",
                                    "overwrite": "true"})

    # print(response.json(), response.url)
    parse_href = response.json()['href']
    return parse_href



# запись файла с номером телефона и айди пользователя
def write_to_file(user_id, user_phone_num):
    text = get_text_from_file()
    text[str(user_id)] = str(user_phone_num)
    return text


def upload_to_disk(user_id, user_phone_num):
    to_download_from_link = getting_link_to_upload()
    # link=f"https://cloud-api.yandex.net/v1/disk/resources/download/?path={path}"
    data = json.dumps(write_to_file(user_id, user_phone_num))
    file = requests.put(to_download_from_link, data=data)
    return file


print(upload_to_disk('1234567', '+77051234567'))
