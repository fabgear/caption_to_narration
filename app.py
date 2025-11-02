import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- （変更なし）▼▼▼
# ===============================================================
def convert_narration_script(text):
    to_zenkaku_num = str.maketrans('0123456789', '０１２３４５６７８９')
    hankaku_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
    zenkaku_chars = 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９　'
    to_zenkaku_all = str.maketrans(hankaku_chars, zenkaku_chars)
    to_hankaku_time = str.maketrans('０１２３４５６７８９：〜', '0123456789:~')

    lines = text.strip().split('\n')
    start_index = -1
    time_pattern = r'(\d{2})[:;](\d{2})[:;](\d{2})(?:[.;](\d{2}))?\s*-\s*(\d{2})[:;](\d{2})[:;](\d{2})(?:[.;](\d{2}))?'
    
    for i, line in enumerate(lines):
        normalized_line = line.strip().translate(to_hankaku_time).replace('~', '-')
        if re.match(time_pattern, normalized_line):
            start_index = i
            break
            
    if start_index == -1: return "エラー：変換可能なタイムコードが見つかりませんでした。"
        
    relevant_lines = lines[start_index:]

    blocks = []
    i = 0
    while i < len(relevant_lines):
        current_line = relevant_lines[i].strip()
        normalized_line = current_line.translate(to_hankaku_time).replace('~', '-')
        if re.match(time_pattern, normalized_line):
            time_val = current_line; text_val = ""
            if i + 1 < len(relevant_lines):
                next_line = relevant_lines[i+1].strip()
                next_normalized = next_line.translate(to_hankaku_time).replace('~', '-')
                if not re.match(time_pattern, next_normalized):
                    text_val = next_line; i += 1
            blocks.append({'time': time_val, 'text': text_val})
        i += 1

    output_lines = []
    for i, block in enumerate(blocks):
        normalized_time_str = block['time'].translate(to_hankaku_time).replace('~', '-')
        time_match = re.match(time_pattern, normalized_time_str)
        if not time_match: continue
        
        groups = time_match.groups()
        start_hh, start_mm, start_ss, start_dec, end_hh, end_mm, end_ss, end_dec = [int(g or 0) for g in groups]

        start_total_seconds = start_ss + start_dec / 100.0
        rounded_sec = round(start_total_seconds)
        if rounded_sec >= 60:
            start_mm += 1; rounded_sec = 0
            if start_mm >= 60:
                start_hh += 1; start_mm = 0
        
        if start_hh > 0: formatted_start_time = f"{start_hh:02d}{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku_num)
        else: formatted_start_time = f"{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku_num)

        speaker_symbol = 'Ｎ'
        text_content = block['text']
        body = ""

        match = re.match(r'^(\S+)\s+(.*)', text_content)
        if match:
            raw_speaker = match.group(1); body = match.group(2).strip()
            if raw_speaker.upper() == 'N': speaker_symbol = 'Ｎ'
            else: speaker_symbol = raw_speaker.translate(to_zenkaku_all)
        else:
            if text_content.upper() == 'N' or text_content == 'Ｎ': body = ""
            elif text_content.startswith('Ｎ '): body = text_content[2:].strip()
            elif text_content.startswith('N '): body = text_content[2:].strip()
            else: body = text_content

        if not body: body = "※注意！本文なし！"
        body = body.translate(to_zenkaku_all)
        
        end_string = ""; add_blank_line = True
        if i + 1 < len(blocks):
            next_time_str = blocks[i+1]['time']
            if next_time_str:
                next_normalized_time = next_time_str.translate(to_hankaku_time).replace('~', '-')
                if re.match(time_pattern, next_normalized_time):
                    next_groups = re.match(time_pattern, next_normalized_time).groups()
                    next_start_hh, next_start_mm, next_start_ss, next_start_dec, _, _, _, _ = [int(g or 0) for g in next_groups]
                    end_total_seconds = (end_hh * 3600) + (end_mm * 60) + end_ss + (end_dec / 100.0)
                    next_start_total_seconds = (next_start_hh * 3600) + (next_start_mm * 60) + next_start_ss + (next_start_dec / 100.0)
                    if next_start_total_seconds - end_total_seconds < 1.0:
                        add_blank_line = False

        if add_blank_line:
            if start_hh != end_hh: formatted_end_time = f"{end_hh:02d}{end_mm:02d}{end_ss:02d}".translate(to_zenkaku_num)
            elif start_mm != end_mm: formatted_end_time = f"{end_mm:02d}{end_ss:02d}".translate(to_zenkaku_num)
            else: formatted_end_time = f"{end_ss:02d}".translate(to_zenkaku_num)
            end_string = f"　（～{formatted_end_time}）"
            
        output_lines.append(f"{formatted_start_time}　　{speaker_symbol}　{body}{end_string}")
        if add_blank_line and i < len(blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# ===============================================================
# ▼▼▼ Streamlitの画面を作る部分 - 【tooltipのバグ修正版】▼▼▼
# ===============================================================
st.set_page_config(page_title="Caption to Narration", page_icon="📝", layout="wide")
st.title('Caption to Narration')

st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)
col1, col2 = st.columns(2)

# --- ▼▼▼【変更点】ここでポップアップで表示したいヘルプテキストを先に定義します ▼▼▼ ---
help_text = """
【機能詳細】  
・ENDタイム(秒のみ)が自動で入ります  
　分をまたぐ時は(分秒)、次のナレーションと繋がる時は割愛されます  
・頭の「N」は自動で全角に変換され未記載の時は自動挿入されます  
　VOや実況などN以外はそのまま適応されます  
・ナレーション本文の半角英数字は全て全角に変換します  
"""

with col1:
    st.header('')
    
    # --- ▼▼▼【変更点】`st.text_area`に、`help`引数を追加します ▼▼▼ ---
    input_text = st.text_area(
        "ナレーション原稿形式に変換します", 
        height=500, 
        placeholder="""キャプションをテキストで書き出した形式
00;00;00;00 - 00;00;02;29
N ああああ

xmlをサイトで変換した形式
００：００：１５　〜　００：００：１８
N ああああ

この２つの形式に対応しています・ペーストして　Ctrl+Enter　を押して下さい
※混在も可能です

""",
        help=help_text # ここに追加！
    )

with col2:
    st.header('')
    if input_text:
        try:
            converted_text = convert_narration_script(input_text)
            st.text_area("コピーしてお使いください", value=converted_text, height=500)
        except Exception as e:
            st.error(f"エラーが発生しました。テキストの形式を確認してください。\n\n詳細: {e}")

# --- フッター（コピーライト表記）は変更なし ---
st.markdown("---")
st.caption("Created by kimika Inc.")
