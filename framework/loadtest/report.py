import json

import allure


def attach_load_summary(title, **metrics):
    """부하 지표를 Allure 첨부파일로 남긴다"""
    allure.attach(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        name=title,
        attachment_type=allure.attachment_type.JSON,
    )
