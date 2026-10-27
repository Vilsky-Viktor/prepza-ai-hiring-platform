import pytest
from prepza_common.i18n.text_language import text_language

# Short job descriptions as people paste them, each full of English tech terms.
JOBS = {
    "en": "We are looking for a backend developer with experience in Python and PostgreSQL.",
    "ru": "Ищем Senior Python разработчика: Django, FastAPI, PostgreSQL, Redis, Docker.",
    "uk": "Шукаємо Python-розробника з досвідом роботи з Django та PostgreSQL. Віддалена робота.",
    "es": "Buscamos un desarrollador backend con experiencia en Python y PostgreSQL para nuestro equipo.",
    "pt": "Vaga para desenvolvedor backend com experiência em Python e PostgreSQL. Você vai trabalhar em equipe.",
    "de": "Wir suchen einen Backend-Entwickler mit Erfahrung in Python und PostgreSQL für unser Team.",
    "fr": "Nous recherchons un développeur backend avec une expérience en Python et PostgreSQL pour notre équipe.",
    "it": "Cerchiamo uno sviluppatore backend con esperienza in Python e PostgreSQL per il nostro team.",
    "pl": "Szukamy programisty backend z doświadczeniem w Python i PostgreSQL. Oferujemy pracę zdalną.",
    "nl": "Wij zoeken een backend developer met ervaring in Python en PostgreSQL voor ons team.",
    "tr": "Python ve PostgreSQL deneyimi olan bir backend geliştirici arıyoruz. Ekip çalışması için.",
    "ar": "نبحث عن مطور خلفية لديه خبرة في Python و PostgreSQL للانضمام إلى فريقنا.",
    "he": "אנחנו מחפשים מפתח צד שרת עם ניסיון ב-Python ו-PostgreSQL להצטרף לצוות שלנו.",
    "fa": "ما به دنبال یک برنامه‌نویس بک‌اند با تجربه کار با Python و PostgreSQL هستیم.",
    "ja": "PythonとPostgreSQLの経験があるバックエンドエンジニアを募集しています。",
    "zh": "我们正在招聘有Python和PostgreSQL经验的后端开发工程师。",
    "ko": "Python과 PostgreSQL 경험이 있는 백엔드 개발자를 찾고 있습니다.",
    "hi": "हमें Python और PostgreSQL के अनुभव वाले बैकएंड डेवलपर की तलाश है।",
    "id": "Kami mencari pengembang backend yang memiliki pengalaman dengan Python dan PostgreSQL.",
    "th": "เรากำลังมองหานักพัฒนาแบ็กเอนด์ที่มีประสบการณ์ด้าน Python และ PostgreSQL",
    "vi": "Chúng tôi cần lập trình viên backend có kinh nghiệm làm việc với Python và PostgreSQL.",
    "fil": "Naghahanap kami ng backend developer na may karanasan sa Python at PostgreSQL para sa aming team.",
    "et": "Otsime backend-arendajat, kellel on kogemus Pythoni ja PostgreSQL-iga ning soov meie tiimiga liituda.",
}


@pytest.mark.parametrize(("expected", "text"), JOBS.items())
def test_the_pasted_text_decides_the_language(expected, text):
    # The interface's language doesn't matter while the text has words to go by.
    assert text_language(text, "ru" if expected != "ru" else "en") == expected


def test_a_russian_text_full_of_tech_terms_is_still_russian():
    assert text_language("Python, Django, PostgreSQL — опыт от 3 лет", "en") == "ru"


def test_a_job_title_alone_is_english_whatever_the_interface():
    assert text_language("Senior Python developer", "ru") == "en"


def test_an_english_text_naming_a_russian_city_stays_english():
    text = "Backend engineer in our Москва office: Python, SQL and cloud infrastructure."

    assert text_language(text, "ru") == "en"


def test_a_text_without_letters_takes_the_interfaces_language():
    assert text_language("123 — 456", "ru") == "ru"


def test_a_latin_text_without_common_words_takes_the_callers_unknown():
    assert text_language("Kubernetes, Terraform", unknown="de") == "de"
    assert text_language("Kubernetes, Terraform") == "en"
