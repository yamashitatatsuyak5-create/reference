import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json
import urllib.parse

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
    # 最新の高速モデルを使用
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    # AIへの指示（JSON形式で確実に出力させる）
    prompt = """
    以下の論文テキストの末尾にある「参考文献（References / Bibliography）」のセクションを見つけ出し、
    記載されているすべての文献を抽出してください。
    
    出力は以下のJSONフォーマットの配列のみとし、それ以外の文章（Markdownの```jsonなどの記号も含む）は一切出力しないでください。

    [
      {
        "title": "論文のタイトル",
        "authors": "著者名",
        "year": "発行年"
      },
      ...
    ]

    --- 論文テキスト ---
    """ + text
    
    response = model.generate_content(prompt)
    
    # AIの返答（文字列）をPythonで扱えるデータ（リスト）に変換
    try:
        # 不要なMarkdown記号が含まれていた場合に備えて除去
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        ref_list = json.loads(clean_text)
        return ref_list
    except json.JSONDecodeError:
        return None

# --- Streamlit UI の構築 ---
st.title("🔗 参考文献 芋づる式URLメイカー")
st.write("論文PDFをアップロードすると、AIが参考文献リストを抽出し、一瞬で各データベースの検索リンク付きリストを作成します！")

api_key = st.text_input("Gemini APIキーを入力してください", type="password")
uploaded_file = st.file_uploader("元となる論文PDFをアップロード", type=["pdf"])

if api_key and uploaded_file is not None:
    if st.button("参考文献リストを作成する"):
        with st.spinner("PDFを解析し、参考文献のリストと検索リンクを生成中です..."):
            try:
                # 1. テキスト抽出
                paper_text = extract_text_from_pdf(uploaded_file)
                
                # 2. AIによる参考文献の抽出
                references = extract_references(paper_text, api_key)
                
                if references:
                    st.success(f"{len(references)} 件の参考文献を抽出しました！")
                    st.markdown("### 📚 参考文献リンク一覧")
                    
                    # 3. リストを展開して複数の検索リンクを自動生成
                    for ref in references:
                        title = ref.get('title', 'タイトル不明')
                        authors = ref.get('authors', '著者不明')
                        year = ref.get('year', '年不明')
                        
                        # タイトルをURL用の文字に変換（quote_plusを使用して記号エラーを防止）
                        encoded_title = urllib.parse.quote_plus(title)
                        
                        # 各種データベースの検索URLを作成
                        scholar_url = f"[https://scholar.google.co.jp/scholar?q=](https://scholar.google.co.jp/scholar?q=){encoded_title}"
                        cinii_url = f"[https://cir.nii.ac.jp/all?q=](https://cir.nii.ac.jp/all?q=){encoded_title}"
                        google_url = f"[https://www.google.com/search?q=](https://www.google.com/search?q=){encoded_title}"
                        
                        # Googleの「PDF指定検索」コマンドを使ったURL
                        pdf_search_url = f"[https://www.google.com/search?q=](https://www.google.com/search?q=){encoded_title}+filetype:pdf"
                        
                        # 論文のタイトルと、4つの検索リンクを横に並べて表示するHTML
                        html_content = f"""
                        <div style="margin-bottom: 15px;">
                            <span style="font-weight:bold; font-size:16px;">{title}</span><br>
                            <span style="font-size:14px; color:gray;">👤 著者: {authors} ({year}年)</span><br>
                            <div style="margin-top: 5px;">
                                <a href="{scholar_url}" target="_blank" style="text-decoration:none; background-color:#e0f7fa; color:#006064; padding:3px 8px; border-radius:5px; margin-right:5px; font-size:14px;">🎓 Scholar</a>
                                <a href="{cinii_url}" target="_blank" style="text-decoration:none; background-color:#fff3e0; color:#e65100; padding:3px 8px; border-radius:5px; margin-right:5px; font-size:14px;">📚 CiNii</a>
                                <a href="{google_url}" target="_blank" style="text-decoration:none; background-color:#f3e5f5; color:#4a148c; padding:3px 8px; border-radius:5px; margin-right:5px; font-size:14px;">🔍 Google</a>
                                <a href="{pdf_search_url}" target="_blank" style="text-decoration:none; background-color:#ffebee; color:#b71c1c; padding:3px 8px; border-radius:5px; font-weight:bold; font-size:14px;">📄 PDF直リンクを探す</a>
                            </div>
                        </div>
                        """
                        st.markdown(html_content, unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.error("参考文献の抽出に失敗しました。論文の形式が特殊か、参考文献欄が見つからなかった可能性があります。")
                
            except Exception as e:
                st.error(f"エラーが発生しました。詳細: {e}")
elif not api_key:
    st.info("まずはAPIキーを入力してください。")