import streamlit as st
from PIL import Image
import zipfile
import io

# ページ基本設定
st.set_page_config(
    page_title="画像リサイズツール",
    page_icon="🖼️",
    layout="centered"
)

st.title("🖼️ 画像リサイズツール")
st.markdown("アップロードした画像（JPG/PNG等）のサイズを**2分の1（または指定倍率）**に一括縮小します。＠ポケットの容量節約にご活用ください！")
st.markdown("---")

# --- サイドバー設定 ---
st.sidebar.header("⚙️ リサイズ＆出力設定")

# 1. 縮小倍率
scale_option = st.sidebar.selectbox(
    "縮小倍率を選択",
    options=[0.5, 0.25, 0.75],
    format_func=lambda x: f"{int(x * 100)}% サイズ (1/{int(1/x)})" if x < 1 else f"{int(x * 100)}%",
    index=0  # デフォルト 0.5 (2分の1)
)

# 2. 画質設定
quality = st.sidebar.slider(
    "JPG保存品質 (画質)",
    min_value=50,
    max_value=95,
    value=80,
    step=5,
    help="数値を下げるとファイルサイズがさらに軽くなります。"
)

st.sidebar.markdown("---")

# 3. ダウンロード形式の選択
download_mode = st.sidebar.radio(
    "📥 ダウンロード形式を選択",
    options=["ZIPファイルで一括ダウンロード", "1枚ずつ個別にダウンロード"],
    index=0
)

# --- メイン画面：ファイルアップロード ---
uploaded_files = st.file_uploader(
    "画像をここにドラッグ＆ドロップしてください（複数選択可）",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"📌 {len(uploaded_files)} 件のファイルがアップロードされました。")
    st.markdown("---")
    
    # 共通画像処理関数
    def process_image(file, scale, qual):
        img = Image.open(file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=qual)
        buf.seek(0)
        
        base_name = ".".join(file.name.split('.')[:-1]) if '.' in file.name else file.name
        out_name = f"{base_name}.jpg"
        
        return resized, buf, new_w, new_h, out_name

    # --- モード A: ZIP一括ダウンロード ---
    if download_mode == "ZIPファイルで一括ダウンロード":
        st.info("📦 すべての画像をまとめてZIP形式でダウンロードします。")
        
        if st.button("🚀 リサイズしてZIPを作成する", type="primary"):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"処理中 ({i+1}/{len(uploaded_files)}): {file.name}")
                    try:
                        _, buf, _, _, out_name = process_image(file, scale_option, quality)
                        zip_file.writestr(out_name, buf.getvalue())
                    except Exception as e:
                        st.error(f"ファイル {file.name} の処理エラー: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                status_text.text("✅ すべての処理が完了しました！")
                progress_bar.empty()
                
            zip_buffer.seek(0)
            st.success("🎉 ZIPファイルの準備ができました！下のボタンからダウンロードしてください。")
            st.download_button(
                label="📦 リサイズ済み画像を一括ダウンロード (ZIP)",
                data=zip_buffer,
                file_name="atpocket_resized_images.zip",
                mime="application/zip",
                type="primary"
            )

    # --- モード B: 個別ダウンロード ---
    else:
        st.info("📥 画面上でプレビューを確認しながら、1枚ずつ個別にダウンロードできます。")
        st.markdown("---")
        
        for i, file in enumerate(uploaded_files):
            try:
                resized_img, buf, w, h, out_name = process_image(file, scale_option, quality)
                file_size_kb = buf.getbuffer().nbytes / 1024
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(resized_img, caption=f"{w} x {h} px", width=120)
                with col2:
                    st.markdown(f"**ファイル名:** `{out_name}`")
                    st.markdown(f"**容量:** `{file_size_kb:.1f} KB`")
                    st.download_button(
                        label="📥 この画像をダウンロード",
                        data=buf,
                        file_name=out_name,
                        mime="image/jpeg",
                        key=f"dl_btn_{i}"
                    )
                st.markdown("---")
                
            except Exception as e:
                st.error(f"ファイル {file.name} の処理中にエラーが発生しました: {e}")
else:
    st.info("💡 ヒント: 左側サイドバーで「ZIP一括」か「個別」かを選択し、画像をアップロードしてください。")
