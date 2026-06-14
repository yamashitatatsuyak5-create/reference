import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json
import urllib.parse
import re

# --- PDFからテキストを抽出する関数 ---
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# --- AIに参考文献リストを抽出させる関数 ---
def extract_references(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = """
    以下の論文テキストの末尾にある「参考文献（References / Bibliography）」のセクションを見つけ出し、
    記載されているすべての文献を抽出してください。
    
    出力は以下のJSONフォーマットの配列のみとし、それ以外の文章は一切出力しないでください。
    [
      {
        "title": "論文のタイトル",
        "authors": "著者名",
        "year": "発行年"
      }
    ]
    --- 論文テキスト ---
    """ + text
    
    try:
        response = model.generate_content(prompt)
        # 💡 AIの返答から、JSONのカッコ [...] の部分だけを確実に抜き出す（エラー防止）
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            clean_text = match.group(0)
            ref_list = json.loads(clean_text)
            return ref_list
        else:
            return None
    except Exception as e:
        # AIが処理に失敗した場合はNoneを返す
        return None

# --- Streamlit UI の構築 ---
st.title("🔗 参考文献 芋づる式URLメイカー")
st.write("論文PDFをアップロードすると、AIが参考文献リストを抽出し、検索ボタンを自動生成します！")

api_key = st.text_input("Gemini APIキーを入力してください", type="password")
uploaded_file = st.file_uploader("元となる論文PDFをアップロード", type=["pdf"])

if api_key and uploaded_file is not None:
    if st.button("参考文献リストを作成する"):
        with st.spinner("PDFを解析し、参考文献のリストと検索リンクを生成中です..."):
            
            # 1. テキスト抽出
            paper_text = extract_text_from_pdf(uploaded_file)
            
            # 2. AIによる参考文献の抽出
            references = extract_references(paper_text, api_key)
            
            if references:
                st.success(f"{len(references)} 件の参考文献を抽出しました！")
                st.markdown("### 📚 参考文献リンク一覧")
                
                # 3. リストを展開してボタンを自動生成（安全な公式機能を使用）
                for ref in references:
                    title = ref.get('title', 'タイトル不明')
                    authors = ref.get('authors', '著者不明')
                    year = ref.get('year', '年不明')
                    
                    # 文献の情報を表示
                    st.markdown(f"#### {title}")
                    st.markdown(f"👤 **著者:** {authors} ({year}年)")
                    
                    # タイトルをURL用の文字に変換
                    encoded_title = urllib.parse.quote_plus(title)
                    
                    # 各種データベースの検索URLを作成
                    scholar_url = f"https://scholar.google.co.jp/scholar?q={encoded_title}"
                    cinii_url = f"https://cir.nii.ac.jp/all?q={encoded_title}"
                    google_url = f"https://www.google.com/search?q={encoded_title}"
                    pdf_search_url = f"https://www.google.com/search?q={encoded_title}+filetype:pdf"
                    
                    # 💡 Streamlit公式の安全なボタン機能（st.link_button）を横並びで配置
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.link_button("🎓 Scholar", scholar_url, use_container_width=True)
                    with col2:
                        st.link_button("📚 CiNii", cinii_url, use_container_width=True)
                    with col3:
                        st.link_button("🔍 Google", google_url, use_container_width=True)
                    with col4:
                        st.link_button("📄 PDF検索", pdf_search_url, use_container_width=True)
                    
                    st.markdown("---")
            else:
                st.error("参考文献の抽出に失敗しました。論文の形式が特殊か、AIがテキストを読み取れなかった可能性があります。")

elif not api_key:
    st.info("まずはAPIキーを入力してください。")
