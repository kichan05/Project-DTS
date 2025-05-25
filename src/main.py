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

    base_dir = os.getenv("FLET_APP_STORAGE_DATA") or os.getcwd()
    os.makedirs(base_dir, exist_ok=True)

    now = datetime.now()
    file_name = now.strftime("%Y%m%d-%H시 %M분 %S초.mp3")
    full_path = os.path.join(base_dir, file_name)

    with openai.audio.speech.with_streaming_response.create(
            model=model,
            voice="coral",
            input=script,
            instructions="재미있는 학교 선생님이 학생에게 설명해주는것 처럼 재미있게 해줘",
    ) as res:
        res.stream_to_file(full_path)


def main(page: ft.Page):
    page.title = "자동 TTS"
    page.scroll = ft.ScrollMode.AUTO
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
        loading_dialog_message.value = "파일을 업로드 하는중입니다."
        page.open(loading_dialog)
        page.update()

        try:
            files = upload_file(selected_file_list)
            loading_dialog_message.value = "스크립트를 생성하는 중입니다."
            page.update()
            res = ask_gpt(files)
        except Exception as e:
            page.close(loading_dialog)
            error_dialog_content.value = e
            page.open(error_dialog)
            page.update()
            raise e

        gpt_result_view.value = res
        file_upload_view.visible = False
        script_check_view.visible = True

        page.close(loading_dialog)
        page.update()

    def on_tts_make_click(e):
        loading_dialog_message.value = "TTS 파일을 생성하는 중입니다."
        page.open(loading_dialog)
        page.update()

        try:
            make_tts(gpt_result_view.value)
        except Exception as e:
            page.close(loading_dialog)

            error_dialog_content.value = e
            page.open(error_dialog)
            page.update()
            raise e

        script_check_view.visible = False
        success_view.visible = True

        page.close(loading_dialog)
        page.update()

    def on_reset_click(e):
        success_view.visible = False
        file_upload_view.visible = True

        selected_file_list.clear()
        page.update()

    gpt_result_view = ft.TextField(max_lines=1000)
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    loading_dialog_message = ft.Text("파일을 업로드 하는중입니다.")
    loading_dialog = ft.AlertDialog(
        content=ft.Column([
            ft.ProgressRing(),
            loading_dialog_message
        ],
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        modal=True
    )

    error_dialog_content = ft.Text("오류가 발생했습니다")
    error_dialog = ft.AlertDialog(
        title=ft.Text("오류가 발생했습니다."),
        content=ft.Row([
            ft.Icon(ft.Icons.ERROR),
            error_dialog_content,
        ]),
        actions=[
            ft.ElevatedButton("닫기", on_click=lambda e: page.close(error_dialog))
        ],
    )

    file_list = ft.Column()

    file_upload_view = ft.Column([
        ft.ElevatedButton(
            "파일 선택",
            icon=ft.Icons.FILE_OPEN,
            on_click=lambda _: pick_files_dialog.pick_files(
                allow_multiple=True
            )
        ),
        file_list,
        ft.ElevatedButton(
            "파일 업로드",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=on_upload_click
        ),
    ],
        visible=True,
    )

    script_check_view = ft.Column([
        ft.Text("GPT가 생성한 스크립트 입니다"),
        ft.Text("확인과 수정 후 TTS를 생성해주세요"),
        gpt_result_view,
        ft.ElevatedButton(
            "TTS 생성",
            icon=ft.Icons.AUDIO_FILE,
            on_click=on_tts_make_click
        ),
    ],
        visible=False,
    )

    success_view = ft.Column([
        ft.Text("TTS 파일 생성을 성공했습니다"),
        ft.ElevatedButton("처음으로", icon=ft.Icons.LOCK_RESET, on_click=on_reset_click)
    ], visible=False,
    )

    page.add(file_upload_view, script_check_view, success_view)


ft.app(main, assets_dir="assets")
