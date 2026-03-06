import re
import html
import json
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="MISHARP SEO Generator",
    page_icon="🔎",
    layout="wide",
)


AUTHOR_DEFAULT = "MISHARP 미샵"
BRAND_NAME = "미샵 MISHARP"
CORE_KEYWORDS = [
    "4050여성패션",
    "4050여성코디",
    "중년여성코디",
    "여성출근룩",
    "체형커버코디",
    "간절기코디",
    "여성데일리룩",
    "중년여성패션",
    "모임룩코디",
    "학모룩코디",
]

CATEGORY_MAP = {
    "니트": ["여성니트", "출근룩니트", "단정한코디", "체형커버니트"],
    "가디건": ["여성가디건", "간절기가디건", "단정한코디", "모임룩추천"],
    "블라우스": ["여성블라우스", "단정한블라우스", "출근룩코디", "모임룩추천"],
    "셔츠": ["여성셔츠", "스트라이프셔츠", "출근룩코디", "단정한코디"],
    "티셔츠": ["여성티셔츠", "슬리밍티셔츠", "배커버티셔츠", "체형커버코디"],
    "맨투맨": ["여성맨투맨", "루즈핏맨투맨", "데일리룩추천", "간절기코디"],
    "자켓": ["여성자켓", "트위드자켓", "오피스룩", "하객룩코디"],
    "점퍼": ["여성점퍼", "간절기점퍼", "루즈핏아우터", "데일리룩추천"],
    "바바리": ["여성트렌치", "바바리코트", "간절기아우터", "단정한코디"],
    "코트": ["여성코트", "하프코트", "핸드메이드코트", "모임룩추천"],
    "슬랙스": ["여성슬랙스", "와이드슬랙스", "출근룩팬츠", "중년여성슬랙스"],
    "팬츠": ["여성팬츠", "밴딩팬츠", "와이드팬츠", "체형커버코디"],
    "스커트": ["여성스커트", "롱스커트", "모임룩코디", "단정한코디"],
    "원피스": ["여성원피스", "하객룩원피스", "모임룩추천", "4050원피스"],
    "조끼": ["여성베스트", "니트조끼", "레이어드코디", "단정한코디"],
}

STYLE_HINTS = {
    "배색": ["배색", "단정한코디", "레이어드룩"],
    "카라": ["카라", "단정한코디", "출근룩"],
    "슬리밍": ["슬리밍", "날씬해보이는코디", "체형커버코디"],
    "꼬임": ["꼬임", "복부커버", "여성스러운코디"],
    "루즈핏": ["루즈핏", "군살커버", "데일리룩"],
    "와이드": ["와이드", "편한슬랙스", "출근룩코디"],
    "밴딩": ["밴딩", "편한팬츠", "데일리룩추천"],
    "트위드": ["트위드", "하객룩코디", "모임룩추천"],
    "아워 글래스": ["아워글래스", "라인살림", "여성자켓"],
    "후드": ["후드", "캐주얼코디", "간절기코디"],
    "스트라이프": ["스트라이프", "클래식셔츠", "출근룩코디"],
}

ENGLISH_KEYWORDS_COMMON = [
    "korean fashion",
    "women fashion",
    "women clothing",
    "k fashion",
]

ENGLISH_KEYWORDS_BY_CATEGORY = {
    "니트": ["women knit", "women sweater", "korean knitwear"],
    "가디건": ["women cardigan", "knit cardigan women", "korean cardigan"],
    "블라우스": ["women blouse", "office blouse women", "korean blouse"],
    "셔츠": ["women shirt", "striped shirt women", "office look women"],
    "티셔츠": ["women t shirt", "slim fit tee women", "daily look women"],
    "맨투맨": ["women sweatshirt", "casual top women", "daily look women"],
    "자켓": ["women jacket", "tweed jacket women", "korean jacket"],
    "점퍼": ["women jumper", "light outer women", "casual jacket women"],
    "바바리": ["women trench coat", "trench coat women", "korean trench"],
    "코트": ["women coat", "handmade coat women", "half coat women"],
    "슬랙스": ["women slacks", "wide slacks women", "office pants women"],
    "팬츠": ["women pants", "banding pants women", "wide pants women"],
    "스커트": ["women skirt", "long skirt women", "office skirt women"],
    "원피스": ["women dress", "occasion dress women", "korean dress"],
    "조끼": ["women vest", "knit vest women", "layered look women"],
}

STOP_WORDS = {
    "미샵", "misharp", "상품", "신상", "추천", "여성", "상의", "하의", "기획", "best",
    "new", "sale", "md", "룩", "코디"
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_html(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def extract_meta(soup: BeautifulSoup, key: str, attr: str = "property") -> str:
    tag = soup.find("meta", attrs={attr: key})
    if tag and tag.get("content"):
        return clean_text(tag.get("content"))
    return ""


def normalize_product_name(name: str) -> str:
    name = clean_text(name)
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"\([^\)]+\)", "", name)
    name = re.sub(r"\s+_\s*\d+$", "", name)
    name = re.sub(r"\s{2,}", " ", name)
    return name.strip(" -|")


def find_product_name(soup: BeautifulSoup) -> str:
    selectors = [
        "meta[property='og:title']",
        "meta[name='twitter:title']",
        "h1",
        ".headingArea h2",
        ".headingArea h1",
        ".prd-name",
        ".product_title",
        "title",
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if not el:
            continue
        value = el.get("content") if el.name == "meta" else el.get_text(" ", strip=True)
        value = normalize_product_name(value)
        if value:
            return value
    return ""


def find_description_text(soup: BeautifulSoup) -> str:
    candidates = [
        extract_meta(soup, "og:description"),
        extract_meta(soup, "description", attr="name"),
        extract_meta(soup, "twitter:description", attr="name"),
    ]
    for text in candidates:
        if text:
            return text

    texts = []
    selectors = [
        "#prdDetail", ".prd-detail", ".detailArea", "#tabProduct", ".product-detail",
        ".cont", ".detail", ".infoArea"
    ]
    for selector in selectors:
        block = soup.select_one(selector)
        if block:
            text = clean_text(block.get_text(" ", strip=True))
            if len(text) > 80:
                texts.append(text)
    if texts:
        texts.sort(key=len, reverse=True)
        return texts[0]
    return ""


def find_image_url(soup: BeautifulSoup, base_url: str) -> str:
    og_image = extract_meta(soup, "og:image")
    if og_image:
        return urljoin(base_url, og_image)

    for selector in [".keyImg img", ".thumbnail img", ".prdImg img", "img.BigImage"]:
        img = soup.select_one(selector)
        if img and img.get("src"):
            return urljoin(base_url, img.get("src"))
    return ""


def guess_category(product_name: str, description: str) -> str:
    corpus = f"{product_name} {description}"
    for category in CATEGORY_MAP:
        if category in corpus:
            return category
    return "의류"


def extract_materials(description: str) -> list[str]:
    materials = []
    for token in ["코튼", "면", "폴리에스터", "레이온", "비스코스", "스판", "아크릴", "울", "린넨", "나일론"]:
        if token in description:
            materials.append(token)
    return materials[:3]


def extract_fit_style(product_name: str, description: str) -> list[str]:
    corpus = f"{product_name} {description}"
    hits = []
    for key in ["루즈핏", "정핏", "와이드", "슬리밍", "아워 글래스", "밴딩", "배색", "카라", "랩", "트위드", "후드", "꼬임"]:
        if key in corpus:
            hits.append(key)
    return hits


def build_title(product_name: str, category: str, styles: list[str]) -> str:
    main = product_name
    style_phrase = ""
    target_phrase = "4050 여성 코디"

    if category in ["니트", "가디건", "블라우스", "셔츠"]:
        target_phrase = "4050 여성 출근룩"
    elif category in ["슬랙스", "팬츠", "스커트"]:
        target_phrase = "중년 여성 코디"
    elif category in ["자켓", "코트", "바바리", "점퍼"]:
        target_phrase = "모임룩 아우터"
    elif category == "원피스":
        target_phrase = "4050 여성 모임룩"

    if "배색" in styles or "카라" in styles:
        style_phrase = "단정한 레이어드룩"
    elif "슬리밍" in styles or "꼬임" in styles:
        style_phrase = "체형커버 데일리룩"
    elif "루즈핏" in styles:
        style_phrase = "군살커버 데일리룩"
    elif "와이드" in styles or "밴딩" in styles:
        style_phrase = "편한 출근룩"
    elif "트위드" in styles or "아워 글래스" in styles:
        style_phrase = "단정한 모임룩"
    else:
        if category in ["니트", "가디건", "블라우스", "셔츠"]:
            style_phrase = "단정한 코디"
        elif category in ["슬랙스", "팬츠", "스커트"]:
            style_phrase = "편한 출근룩"
        else:
            style_phrase = "여성 데일리룩"

    title = f"{main} {style_phrase} {target_phrase}".strip()
    title = re.sub(r"\s+", " ", title)
    if len(title) > 50:
        title = f"{main} {style_phrase}".strip()
    if len(title) < 30:
        title = f"{main} {style_phrase} {target_phrase}".strip()
    return title[:50].strip()


def shorten_to_range(text: str, min_len: int = 120, max_len: int = 160) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    clipped = text[:max_len]
    last_period = max(clipped.rfind("."), clipped.rfind(" "))
    if last_period > min_len:
        clipped = clipped[:last_period]
    return clipped.strip(" ,.") + "."


def build_description(product_name: str, category: str, description_src: str, styles: list[str], materials: list[str]) -> str:
    feature = []

    if "배색" in styles and "카라" in styles:
        feature.append("배색 카라 포인트로 셔츠를 따로 레이어드하지 않아도 단정한 분위기를 완성")
    elif "슬리밍" in styles or "꼬임" in styles:
        feature.append("라인을 정돈해 보이게 도와주는 디자인으로 복부와 허리선을 자연스럽게 커버")
    elif "루즈핏" in styles:
        feature.append("여유 있는 실루엣으로 상체 군살을 편안하게 감싸주는 핏")
    elif "와이드" in styles or "밴딩" in styles:
        feature.append("편안한 착용감과 깔끔한 실루엣을 함께 잡아주는 팬츠")
    elif "트위드" in styles:
        feature.append("단정하면서도 고급스러운 무드를 완성해주는 트위드 타입 디자인")
    else:
        feature.append(f"{product_name} 특유의 깔끔한 실루엣과 활용도 높은 디자인")

    if materials:
        feature.append(f"{', '.join(materials)} 혼용의 편안한 소재감")

    situation = {
        "니트": "출근룩과 모임룩은 물론 데일리 코디까지 부담 없이 활용하기 좋고",
        "가디건": "출근룩과 간절기 데일리룩에 가볍게 걸치기 좋고",
        "블라우스": "출근룩과 단정한 모임룩에 활용하기 좋고",
        "셔츠": "출근룩과 학모룩처럼 단정한 자리에도 잘 어울리고",
        "티셔츠": "데님, 슬랙스, 스커트 어디에나 매치하기 좋고",
        "맨투맨": "주말룩과 편안한 데일리룩에 자연스럽게 어울리고",
        "자켓": "오피스룩, 학모룩, 하객룩처럼 단정한 자리에도 활용하기 좋고",
        "점퍼": "간절기 외출룩과 데일리 아우터로 손이 자주 가고",
        "바바리": "출근길부터 모임 자리까지 분위기 있게 걸치기 좋고",
        "코트": "격식 있는 자리와 일상 모두에 자연스럽게 어울리고",
        "슬랙스": "출근룩과 모임룩 팬츠로 활용도가 높고",
        "팬츠": "데일리룩부터 가벼운 외출룩까지 편안하게 입기 좋고",
        "스커트": "모임룩과 데일리룩 모두 여성스럽게 연출하기 좋고",
        "원피스": "모임룩과 하객룩 같은 자리에 깔끔하게 입기 좋고",
    }.get(category, "다양한 일상 코디에 활용하기 좋고")

    ending = "4050 여성 고객이 단정함과 편안함, 체형 커버를 함께 챙기기에 좋은 아이템입니다"

    sentence = f"{feature[0]}{', ' + feature[1] if len(feature) > 1 else ''}. {situation} {ending}."

    if len(sentence) < 120 and description_src:
        extra = clean_text(description_src)[:60].strip(" ,.")
        sentence = f"{sentence[:-1]} 특히 {extra}."

    return shorten_to_range(sentence)


def tokenize_korean_phrases(product_name: str) -> list[str]:
    parts = re.split(r"[\s/,+\-]+", product_name)
    tokens = []
    for part in parts:
        part = clean_text(part)
        if len(part) < 2:
            continue
        lower = part.lower()
        if lower in STOP_WORDS:
            continue
        tokens.append(part)
    return tokens[:8]


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        key = item.strip().lower()
        if not item or key in seen:
            continue
        seen.add(key)
        output.append(item.strip())
    return output


def build_english_keywords(category: str) -> list[str]:
    keywords = []
    keywords.extend(ENGLISH_KEYWORDS_COMMON)
    keywords.extend(ENGLISH_KEYWORDS_BY_CATEGORY.get(category, []))
    keywords = dedupe_keep_order(keywords)
    return keywords[:5]


def build_keywords(product_name: str, category: str, styles: list[str]) -> list[str]:
    korean_keywords = []
    korean_keywords.extend(CORE_KEYWORDS)

    if category in CATEGORY_MAP:
        korean_keywords.extend(CATEGORY_MAP[category])

    for style in styles:
        korean_keywords.extend(STYLE_HINTS.get(style, []))

    tokens = tokenize_korean_phrases(product_name)
    korean_keywords.extend(tokens)

    if category != "의류":
        korean_keywords.append(f"4050여성{category}")
        korean_keywords.append(f"중년여성{category}")

    if category in ["니트", "가디건", "블라우스", "셔츠", "티셔츠"]:
        korean_keywords.extend(["단정한코디", "출근룩추천", "모임룩추천"])
    elif category in ["슬랙스", "팬츠", "스커트"]:
        korean_keywords.extend(["편한출근룩", "체형커버팬츠", "데일리룩추천"])
    else:
        korean_keywords.extend(["간절기코디", "여성아우터추천", "4050모임룩"])

    korean_keywords = dedupe_keep_order(korean_keywords)
    english_keywords = build_english_keywords(category)

    final_keywords = korean_keywords[:20] + english_keywords
    return dedupe_keep_order(final_keywords)[:25]


def build_alt_text(product_name: str, category: str, styles: list[str]) -> str:
    compact = product_name.replace(" ", "")
    if len(compact) <= 10:
        return compact

    for style in ["배색카라", "슬리밍", "와이드", "루즈핏", "트위드", "후드", "밴딩"]:
        if style in compact:
            if category != "의류" and category not in compact:
                return f"{style}{category}"
            return style

    if category != "의류":
        return category if len(category) <= 6 else compact[:6]
    return compact[:8]


# ---------------------------
# 추가 생성 항목
# ---------------------------
def build_slug(product_name: str, category: str) -> str:
    en_map = {
        "니트": "knit",
        "가디건": "cardigan",
        "블라우스": "blouse",
        "셔츠": "shirt",
        "티셔츠": "tshirt",
        "맨투맨": "sweatshirt",
        "자켓": "jacket",
        "점퍼": "jumper",
        "바바리": "trench",
        "코트": "coat",
        "슬랙스": "slacks",
        "팬츠": "pants",
        "스커트": "skirt",
        "원피스": "dress",
        "조끼": "vest",
        "의류": "fashion",
    }
    base = en_map.get(category, "fashion")
    name_part = normalize_product_name(product_name).lower()
    name_part = re.sub(r"[^a-z0-9가-힣\s-]", "", name_part)
    name_part = re.sub(r"\s+", "-", name_part).strip("-")
    if not name_part:
        return f"misharp-{base}"
    return f"{name_part}-{base}"[:60].strip("-")


def build_h1_title(product_name: str, category: str) -> str:
    prefix_map = {
        "니트": "4050 여성 니트 추천",
        "가디건": "4050 여성 가디건 추천",
        "블라우스": "중년 여성 블라우스 추천",
        "셔츠": "4050 여성 셔츠 코디",
        "티셔츠": "체형커버 티셔츠 추천",
        "맨투맨": "데일리 맨투맨 추천",
        "자켓": "4050 여성 자켓 추천",
        "점퍼": "간절기 점퍼 추천",
        "바바리": "4050 여성 바바리 코디",
        "코트": "중년 여성 코트 추천",
        "슬랙스": "4050 여성 슬랙스 추천",
        "팬츠": "편한 팬츠 추천",
        "스커트": "중년 여성 스커트 코디",
        "원피스": "4050 여성 원피스 추천",
        "조끼": "레이어드 조끼 코디",
    }
    prefix = prefix_map.get(category, "4050 여성 코디 추천")
    return f"{prefix} {product_name}".strip()


def build_longtail_keywords(product_name: str, category: str, styles: list[str]) -> list[str]:
    keywords = []

    if category == "니트":
        keywords.extend([
            f"4050 여성 {product_name} 코디",
            f"중년 여성 출근룩 {category}",
            f"단정한 {category} 추천",
            f"4050 여성 {category} 코디",
        ])
    elif category in ["슬랙스", "팬츠"]:
        keywords.extend([
            f"4050 여성 {product_name} 추천",
            f"중년 여성 편한 {category}",
            f"출근룩 {category} 추천",
            f"체형커버 {category} 코디",
        ])
    elif category in ["자켓", "코트", "바바리", "점퍼"]:
        keywords.extend([
            f"4050 여성 {product_name} 추천",
            f"모임룩 {category} 코디",
            f"중년 여성 {category} 추천",
            f"간절기 {category} 코디",
        ])
    else:
        keywords.extend([
            f"4050 여성 {product_name} 추천",
            f"중년 여성 {category} 코디",
            f"출근룩 {category} 추천",
            f"모임룩 {category} 추천",
        ])

    if "루즈핏" in styles:
        keywords.append(f"군살커버 {category} 추천")
    if "슬리밍" in styles or "꼬임" in styles:
        keywords.append(f"날씬해보이는 {category} 코디")
    if "배색" in styles or "카라" in styles:
        keywords.append(f"단정한 {category} 코디")

    return dedupe_keep_order(keywords)[:6]


def calculate_seo_score(title: str, description: str, keywords: str, alt_text: str) -> str:
    score = 0
    notes = []

    if 30 <= len(title) <= 50:
        score += 25
    else:
        notes.append("title 길이 조정 필요")

    if 120 <= len(description) <= 160:
        score += 25
    else:
        notes.append("description 길이 조정 필요")

    keyword_count = len([k.strip() for k in keywords.split(",") if k.strip()])
    if 15 <= keyword_count <= 25:
        score += 25
    else:
        notes.append("keywords 개수 점검 필요")

    if alt_text and len(alt_text) <= 12:
        score += 15
    else:
        notes.append("alt 텍스트 최적화 필요")

    if re.search(r"(4050|중년|여성)", title + " " + description + " " + keywords):
        score += 10
    else:
        notes.append("타깃 키워드 보강 필요")

    if score >= 90:
        grade = "매우 좋음"
    elif score >= 75:
        grade = "좋음"
    elif score >= 60:
        grade = "보통"
    else:
        grade = "보완 필요"

    if notes:
        return f"{score}점 / 100점 ({grade}) · 참고: {', '.join(notes)}"
    return f"{score}점 / 100점 ({grade})"


def build_blog_seo_sentence(product_name: str, category: str, styles: list[str], description: str) -> str:
    mood = "단정하면서도 세련된 분위기"
    if "루즈핏" in styles:
        mood = "편안하면서도 군살 커버에 좋은 분위기"
    elif "슬리밍" in styles or "꼬임" in styles:
        mood = "여성스럽고 날씬해 보이는 분위기"
    elif "트위드" in styles:
        mood = "고급스럽고 격식 있는 분위기"
    elif "배색" in styles or "카라" in styles:
        mood = "단정하고 차려입은 듯한 분위기"

    short_desc = clean_text(description)[:80].strip(" .")
    return (
        f"{product_name}는 {mood}를 연출하기 좋은 아이템으로 "
        f"4050 여성의 출근룩, 모임룩, 데일리 코디에 두루 활용하기 좋습니다. "
        f"{short_desc}."
    )


def analyze_product(url: str) -> dict:
    html_text = fetch_html(url)
    soup = BeautifulSoup(html_text, "html.parser")

    product_name = find_product_name(soup)
    description_src = find_description_text(soup)
    image_url = find_image_url(soup, url)
    category = guess_category(product_name, description_src)
    styles = extract_fit_style(product_name, description_src)
    materials = extract_materials(description_src)

    title = build_title(product_name, category, styles)
    author = AUTHOR_DEFAULT
    description = build_description(product_name, category, description_src, styles, materials)
    keywords_list = build_keywords(product_name, category, styles)
    keywords = ", ".join(keywords_list)
    alt_text = build_alt_text(product_name, category, styles)

    slug = build_slug(product_name, category)
    h1_title = build_h1_title(product_name, category)
    longtail_keywords = build_longtail_keywords(product_name, category, styles)
    seo_score = calculate_seo_score(title, description, keywords, alt_text)
    blog_sentence = build_blog_seo_sentence(product_name, category, styles, description)

    return {
        "url": url,
        "product_name": product_name,
        "category": category,
        "styles": styles,
        "materials": materials,
        "image_url": image_url,
        "title": title,
        "author": author,
        "description": description,
        "keywords": keywords,
        "alt_text": alt_text,
        "slug": slug,
        "h1_title": h1_title,
        "longtail_keywords": longtail_keywords,
        "seo_score": seo_score,
        "blog_sentence": blog_sentence,
        "raw_description": description_src,
    }


def copyable_output(label: str, value: str, key: str, height: int = 68) -> None:
    safe_value = html.escape(value or "")
    safe_label = html.escape(label)
    component_html = f"""
    <div style="margin:0 0 10px 0;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div style="font-size:14px;font-weight:600;color:#111827;">{safe_label}</div>
        <button onclick="navigator.clipboard.writeText(document.getElementById('{key}').innerText);this.innerText='✓ 복사됨';setTimeout(()=>this.innerText='복사',1400);"
          style="font-size:12px;padding:4px 10px;border:1px solid #d1d5db;border-radius:8px;background:#fff;cursor:pointer;">복사</button>
      </div>
      <div id="{key}" style="white-space:pre-wrap;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;background:#f9fafb;font-size:14px;line-height:1.6;min-height:{height}px;">{safe_value}</div>
    </div>
    """
    components.html(component_html, height=height + 46)


def render_output(result: dict) -> None:
    st.success("SEO 생성이 완료되었습니다.")

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("생성 결과")

        copyable_output("1. 브라우저 타이틀(title) (카페24 SEO 입력)", result["title"], "copy_title", 52)
        copyable_output("2. 메타태그1 author (카페24 SEO 입력)", result["author"], "copy_author", 52)
        copyable_output("3. 메타태그2 description (카페24 SEO 입력)", result["description"], "copy_description", 92)
        copyable_output("4. 메타태그3 keywords (카페24 SEO 입력)", result["keywords"], "copy_keywords", 145)
        copyable_output("5. 상품 이미지 alt 텍스트 (상품 이미지 ALT)", result["alt_text"], "copy_alt", 52)

        st.markdown("---")

        copyable_output("6. SEO slug (URL / 블로그 주소용)", result["slug"], "copy_slug", 52)
        copyable_output("7. H1 제목 (상세페이지 첫 문장)", result["h1_title"], "copy_h1", 68)
        copyable_output(
            "8. 롱테일 키워드 (블로그 / 콘텐츠 SEO)",
            "\n".join(result["longtail_keywords"]),
            "copy_longtail",
            120,
        )
        copyable_output("9. SEO 점수 (페이지 SEO 품질 참고)", result["seo_score"], "copy_score", 68)
        copyable_output("10. 블로그 SEO 문장 (블로그 / SNS 콘텐츠)", result["blog_sentence"], "copy_blog", 110)

        formatted = (
            f"1. 브라우저 타이틀(title) : {result['title']}\n\n"
            f"2. 메타태그1 author : {result['author']}\n\n"
            f"3. 메타태그2 description : {result['description']}\n\n"
            f"4. 메타태그3 keywords : {result['keywords']}\n\n"
            f"5. 상품 이미지 alt 텍스트 : {result['alt_text']}\n\n"
            f"6. SEO slug : {result['slug']}\n\n"
            f"7. H1 제목 : {result['h1_title']}\n\n"
            f"8. 롱테일 키워드 : {', '.join(result['longtail_keywords'])}\n\n"
            f"9. SEO 점수 : {result['seo_score']}\n\n"
            f"10. 블로그 SEO 문장 : {result['blog_sentence']}"
        )

        copyable_output("전체 복사 (카페24 + 콘텐츠 SEO 참고용)", formatted, "copy_all", 360)
        st.download_button(
            "TXT 다운로드",
            data=formatted,
            file_name="misharp_seo_result.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        st.subheader("분석 요약")
        st.markdown(f"**상품명** : {result['product_name'] or '-'}")
        st.markdown(f"**카테고리 추정** : {result['category']}")
        st.markdown(f"**스타일 키워드 추정** : {', '.join(result['styles']) if result['styles'] else '-'}")
        st.markdown(f"**소재 키워드 추정** : {', '.join(result['materials']) if result['materials'] else '-'}")
        st.markdown(f"**브랜드 표기** : {BRAND_NAME}")
        if result["image_url"]:
            st.image(result["image_url"], caption="대표 이미지", use_container_width=True)
        if result["raw_description"]:
            with st.expander("추출한 설명 텍스트 보기"):
                st.write(result["raw_description"])

        with st.expander("JSON 결과"):
            st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")


def main() -> None:
    st.title("🔎 MISHARP 카페24 SEO 자동 생성기")
    st.caption("상품 URL을 넣으면 카페24 상품등록용 SEO 항목과 콘텐츠 SEO 참고 항목을 함께 생성합니다.")

    with st.container(border=True):
        st.markdown(
            """
            **카페24 입력용 생성 항목**
            - 브라우저 타이틀(title)
            - 메타태그 author
            - 메타태그 description
            - 메타태그 keywords
            - 상품 이미지 alt 텍스트

            **추가 참고용 생성 항목**
            - SEO slug
            - H1 제목
            - 롱테일 키워드
            - SEO 점수
            - 블로그 SEO 문장

            **키워드 구성 방식**
            - 한국어 구매 키워드 중심
            - 마지막에 영어 SEO 키워드 3~5개 자동 포함
            """
        )

    default_url = "https://www.misharp.co.kr/product/detail.html?product_no=28522&cate_no=24&display_group=1"
    url = st.text_input(
        "미샵 상품 URL",
        value=default_url,
        placeholder="https://www.misharp.co.kr/product/detail.html?..."
    )

    col_a, col_b = st.columns([1, 1])
    generate = col_a.button("SEO 생성하기", use_container_width=True, type="primary")
    clear = col_b.button("입력 초기화", use_container_width=True)

    if clear:
        st.rerun()

    if generate:
        if not url.strip():
            st.error("상품 URL을 입력해주세요.")
            return
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            st.error("올바른 URL 형식이 아닙니다.")
            return
        try:
            with st.spinner("상품 정보를 분석하고 SEO를 생성하는 중입니다..."):
                result = analyze_product(url.strip())
            render_output(result)
        except requests.HTTPError as e:
            st.error(f"페이지 요청 중 오류가 발생했습니다: {e}")
        except requests.RequestException as e:
            st.error(f"네트워크 오류가 발생했습니다: {e}")
        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")

    with st.expander("사용 팁"):
        st.markdown(
            """
            1. 미샵 상품 상세 URL을 그대로 붙여넣습니다.
            2. 1~5번 항목은 카페24 SEO 입력란에 사용합니다.
            3. 6~10번 항목은 상세페이지 문장, 블로그, SNS, 콘텐츠 SEO에 활용합니다.
            4. keywords는 한국어 중심으로 구성되고, 영어 키워드가 마지막에 자동 추가됩니다.

            **추천 활용 방식**
            - 신상품 등록 시마다 바로 사용
            - 기존 베스트 상품 SEO 일괄 보강
            - 상세페이지 첫 문장과 블로그 초안까지 함께 활용
            """
        )

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align:center;font-size:13px;color:#6b7280;padding:10px 0;'>
        © 2026 <b>MISHARP 미샵</b>. All rights reserved.<br>
        MISHARP SEO Generator
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
