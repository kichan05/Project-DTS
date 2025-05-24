import openai
from dotenv import load_dotenv
import os
import time
import flet as ft
from flet.core.file_picker import FilePickerFile
from openai import OpenAI
from openai.types import FileObject
from datetime import datetime
import flet_lottie as fl

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def upload_file(files: list[FilePickerFile]) -> list[FileObject]:
    result_files = []

    for file in files:
        f = open(file.path, "rb")
        res = client.files.create(file=f, purpose="user_data")
        result_files.append(res)

    return result_files


def ask_gpt(files: list[FileObject]) -> str:
    model = "gpt-4o-mini"

    content = []

    for file in files:
        content.append({
            "type": "file",
            "file": {"file_id": file.id}
        })

    content.append({
        "type": "text",
        "text": "이 수업자료를 요약헤서 너만의 수업스크립트를 만들어줘"
    })

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )

    return response.choices[0].message.content


def make_tts(script):
    model = "gpt-4o-mini-tts"

    now = datetime.now()
    file_name = now.strftime("%Y%m%d-%H:%M:%S")
    # f = open(file_name, "rb")

    with openai.audio.speech.with_streaming_response.create(
            model=model,
            voice="coral",
            input=script,
            instructions="재미있는 학교 선생님이 학생에게 설명해주는것 처럼 재미있게 해줘",
    ) as res:
        res.stream_to_file(file_name)


def main(page: ft.Page):
    page.title = "자동 TTS"
    selected_file_list: list[FilePickerFile] = []

    def pick_files_result(e: ft.FilePickerResultEvent):
        selected_file_list.extend(e.files)
        refresh_file_list()

    def refresh_file_list():
        file_list.controls.clear()

        for n, file in enumerate(selected_file_list):
            file_list.controls.append(
                ft.Row([
                    ft.Text(f"{n} - {file.name}"),
                    ft.IconButton(ft.Icons.DELETE, on_click=lambda _, p=file.path: delete_file(p))
                ])
            )

        page.update()

    def delete_file(path):
        selected_file_list[:] = list(filter(lambda x: x.path != path, selected_file_list))
        refresh_file_list()

    def on_upload_click(e):
        loading_view.visible = True
        page.open(loading_dialog)
        page.update()

        files = upload_file(selected_file_list)
        res = ask_gpt(files)

        gpt_result_view.value = res
        make_tts(res)

        page.close(loading_dialog)
        loading_view.visible = False
        page.update()

    loading_view = ft.Text("업로드 중", visible=False)
    gpt_result_view = ft.TextField()
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    loading_dialog = ft.AlertDialog(
        content=ft.Column([
            ft.Text("파일을 업로드 하는중입니다."),
        ]),
        modal=True
    )

    file_list = ft.Column()

    page.add(
        ft.Column(
            [
                ft.ElevatedButton(
                    "파일 선택",
                    icon=ft.Icons.FILE_OPEN,
                    on_click=lambda _: pick_files_dialog.pick_files(
                        allow_multiple=True
                    )
                ),
                file_list,
                ft.Row([
                    ft.ElevatedButton(
                        "파일 업로드",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=on_upload_click
                    ),
                    loading_view,
                ]),
                gpt_result_view,
            ]
        )
    )

    page.open(loading_dialog)


ft.app(main, assets_dir="assets")