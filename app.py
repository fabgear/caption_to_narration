import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）▼▼▼
# ===============================================================
def convert_narration_script(text):
    to_zenkaku = str.maketrans('0123456789', '０１２３４５６７８９')
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
        formatted_start_time = f"{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku)

        text_match = re.match(r'([NＮ])\s*(.*)', block['text'])
        body = text_match.group(2).strip() if text_match else block['text'].strip()
        if not body: body = "※注意！本文なし！"
        
        # --- ▼▼▼ ここからが追加するコードです ▼▼▼ ---
        # 変換したい半角文字のリスト
        hankaku = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
        # 対応する全角文字のリスト
        zenkaku = 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９　'
        # 変換テーブルを作成
        zenkaku_table = str.maketrans(hankaku, zenkaku)
        # 実際に本文（body）を変換
        body = body.translate(zenkaku_table)
        # --- ▲▲▲ ここまでが追加したコードです ▲▲▲ ---
        
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
                formatted_end_time = f"{end_ss:02d}".translate(to_zenkaku)
            else:
                formatted_end_time = f"{end_mm:02d}{end_ss:02d}".translate(to_zenkaku)
            end_string = f"　（～{formatted_end_time}）"
            
        output_lines.append(f"{formatted_start_time}　　Ｎ　{body}{end_string}")
        if add_blank_line and i < len(blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)
# ===============================================================
# ▼▼▼ ここからがStreamlitの魔法の部分です ▼▼▼
# ===============================================================
st.set_page_config(layout="wide") # 画面を広く使う設定
st.title('Caption to Narration')

col1, col2 = st.columns(2)

with col1:
    st.header('')
    input_text = st.text_area("Premiereで書き出したキャプションをペーストして [Ctrl+Enter]  ", height=500, placeholder="例\n00;00;00;00 - 00;00;02;29\nＮ　あああ")

with col2:
    st.header('')
    if input_text:
        try:
            converted_text = convert_narration_script(input_text)
            st.text_area("コピーしてお使いください", value=converted_text, height=500)
        except Exception:
            st.error("エラーが発生しました。テキストの形式が正しいか確認してください。")
