import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- 【話者名判定ロジック改善版】▼▼▼
# ===============================================================
def convert_narration_script(text):
    # --- 変換テーブルの準備 ---
    to_zenkaku_num = str.maketrans('0123456789', '０１２３４５６７８９')
    hankaku_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
    zenkaku_chars = 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９　'
    to_zenkaku_all = str.maketrans(hankaku_chars, zenkaku_chars)

    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    blocks = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            blocks.append({'time': lines[i], 'text': lines[i+1]})

    output_lines = []
    for i, block in enumerate(blocks):
        time_match = re.match(r'(\d{2})[:;](\d{2})[:;](\d{2})[.;](\d{2})\s*-\s*(\d{2})[:;](\d{2})[:;](\d{2})[.;](\d{2})', block['time'])
        if not time_match: continue
        
        start_hh, start_mm, start_ss, start_dec, end_hh, end_mm, end_ss, end_dec = [int(g) for g in time_match.groups()]
        
        start_total_seconds = start_ss + start_dec / 100.0
        rounded_sec = round(start_total_seconds)
        if rounded_sec >= 60:
            start_mm += 1
            rounded_sec = 0
        formatted_start_time = f"{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku_num)

        speaker_symbol = 'Ｎ'
        text_content = block['text'].strip()
        
        match = re.match(r'^(\S+)\s+(.*)', text_content)

        if match:
            raw_speaker = match.group(1)
            body = match.group(2).strip()
            
            if raw_speaker.upper() == 'N':
                speaker_symbol = 'Ｎ'
            else:
                speaker_symbol = raw_speaker.translate(to_zenkaku_all)
        else:
            if text_content.startswith('Ｎ '):
                body = text_content[2:].strip()
            elif text_content.startswith('N '):
                 body = text_content[2:].strip()
            else:
                body = text_content

        if not body:
            body = "※注意！本文なし！"
        
        body = body.translate(to_zenkaku_all)
        
        end_string = ""
        add_blank_line = True

        if i + 1 < len(blocks):
            next_time_match = re.match(r'(\d{2})[:;](\d{2})[:;](\d{2})[.;](\d{2})', blocks[i+1]['time'])
            if next_time_match:
                next_start_hh, next_start_mm, next_start_ss, next_start_dec = [int(g) for g in next_time_match.groups()]
                end_total_seconds = (end_hh * 3600) + (end_mm * 60) + end_ss + (end_dec / 100.0)
                next_start_total_seconds = (next_start_hh * 3600) + (next_start_mm * 60) + next_start_ss + (next_start_dec / 100.0)
                if next_start_total_seconds - end_total_seconds < 1.0:
                    add_blank_line = False

        if add_blank_line:
            if start_mm == end_mm:
                formatted_end_time = f"{end_ss:02d}".translate(to_zenkaku_num)
            else:
                formatted_end_time = f"{end_mm:02d}{end_ss:02d}".translate(to_zenkaku_num)
            end_string = f"　（～{formatted_end_time}）"
            
        output_lines.append(f"{formatted_start_time}　　{speaker_symbol}　{body}{end_string}")
        if add_blank_line and i < len(blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# ===============================================================
# ▼▼▼ ここからがStreamlitの画面を作る部分です ▼▼▼
# ===============================================================
st.set_page_config(
    page_title="Caption to Narration",
    page_icon="📝",
    layout="wide"
)
st.title('Caption to Narration')

# --- ▼▼▼ ここにCSSを書き込むための「おまじない」を追加 ▼▼▼ ---
st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.header('') # ヘッダーを空にする
    input_text = st.text_area(
        "Premiereで書き出したキャプションをペーストして Ctrl+Enter ！", 
        height=500, 
        placeholder="""
--例-----------------------------------------------------
00;00;00;00 - 00;00;02;29
N ああああ

00;00;15;14 - 00;00;18;13
VO ああああ

--👇変換されます------------------------------------------

００００　　Ｎ　ああああ　（～０２）

００１５　　ＶＯ　ああああ　（～１８）

----------------------------------------------------------

【変換ルール】
・ＶＯや人名などを除き、半角Ｎは小文字n、無記載の場合は全角Ｎが強制挿入
・半角英数字は全て全角に変換
・ＥＮＤタイムが自動で入りますがナレーション繋がるところは割愛
"""
    )

with col2:
    st.header('') # ヘッダーを空にする
    if input_text:
        try:
            converted_text = convert_narration_script(input_text)
            st.text_area("コピーしてお使いください", value=converted_text, height=500)
        except Exception:
            st.error("エラーが発生しました。テキストの形式が正しいか確認してください。")
