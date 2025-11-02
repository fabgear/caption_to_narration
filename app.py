import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- （ver2.1：最終Hマーカー修正）▼▼▼
# ===============================================================
def convert_narration_script(text):
    # --- 設定値 ---
    FRAME_RATE = 30.0
    CONNECTION_THRESHOLD = 1.0 + (10.0 / FRAME_RATE)

    to_zenkaku_num = str.maketrans('0123456789', '０１２３４５６７８９')
    hankaku_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
    zenkaku_chars = 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９　'
    to_zenkaku_all = str.maketrans(hankaku_chars, zenkaku_chars)
    to_hankaku_time = str.maketrans('０１２３４５６７８９：〜', '0123456789:~')

    lines = text.strip().split('\n')
    start_index = -1
    time_pattern = r'(\d{2})[:;](\d{2})[:;](\d{2})[;.](\d{2})\s*-\s*(\d{2})[:;](\d{2})[:;](\d{2})[;.](\d{2})'
    
    for i, line in enumerate(lines):
        line_with_frames = re.sub(r'(\d{2}:\d{2}:\d{2})(?![:.]\d{2})', r'\1.00', line)
        normalized_line = line_with_frames.strip().translate(to_hankaku_time).replace('~', '-')
        if re.match(time_pattern, normalized_line):
            start_index = i
            break
            
    if start_index == -1: return "エラー：変換可能なタイムコード（フレーム情報を含む形式）が見つかりませんでした。"
        
    relevant_lines = lines[start_index:]

    blocks = []
    i = 0
    while i < len(relevant_lines):
        current_line = relevant_lines[i].strip()
        line_with_frames = re.sub(r'(\d{2}:\d{2}:\d{2})(?![:.]\d{2})', r'\1.00', current_line)
        normalized_line = line_with_frames.translate(to_hankaku_time).replace('~', '-')

        if re.match(time_pattern, normalized_line):
            time_val = current_line; text_val = ""
            if i + 1 < len(relevant_lines):
                next_line = relevant_lines[i+1].strip()
                next_normalized_line = re.sub(r'(\d{2}:\d{2}:\d{2})(?![:.]\d{2})', r'\1.00', next_line).translate(to_hankaku_time).replace('~', '-')
                if not re.match(time_pattern, next_normalized_line):
                    text_val = next_line; i += 1
            blocks.append({'time': time_val, 'text': text_val})
        i += 1

    output_lines = []
    
    parsed_blocks = []
    for block in blocks:
        line_with_frames = re.sub(r'(\d{2}:\d{2}:\d{2})(?![:.]\d{2})', r'\1.00', block['time'])
        normalized_time_str = line_with_frames.translate(to_hankaku_time).replace('~', '-')
        time_match = re.match(time_pattern, normalized_time_str)
        if not time_match: continue
        
        groups = time_match.groups()
        start_hh, start_mm, start_ss, start_fr, end_hh, end_mm, end_ss, end_fr = [int(g or 0) for g in groups]
        parsed_blocks.append({
            'start_hh': start_hh, 'start_mm': start_mm, 'start_ss': start_ss, 'start_fr': start_fr,
            'end_hh': end_hh, 'end_mm': end_mm, 'end_ss': end_ss, 'end_fr': end_fr,
            'text': block['text']
        })

    previous_end_hh = -1 # 初期値を-1に戻す

    for i, block in enumerate(parsed_blocks):
        start_hh, start_mm, start_ss, start_fr = block['start_hh'], block['start_mm'], block['start_ss'], block['start_fr']
        end_hh, end_mm, end_ss, end_fr = block['end_hh'], block['end_mm'], block['end_ss'], block['end_fr']

        # ▼▼▼【ver2.1 変更点】Hマーカーは、現在のブロックの開始時が直前のブロックの終了時と異なるときに入れる ▼▼▼
        should_insert_h_marker = False
        
        if i == 0:
            if start_hh > 0:
                 should_insert_h_marker = True
            previous_end_hh = end_hh # 最初のブロックの終了時を記録
        
        else:
            # 現在のブロックの開始時が、直前のブロックの終了時より大きい場合
            if start_hh > previous_end_hh:
                 should_insert_h_marker = True

        if should_insert_h_marker:
             output_lines.append("")
             output_lines.append(f"＜{str(start_hh).translate(to_zenkaku_num)}Ｈ＞")
             output_lines.append("")
             
        previous_end_hh = end_hh # 現在のブロックの終了時を記録
        # ▲▲▲【ver2.1 変更点】ここまで ▼▼▼

        # ... (開始時間、本文、終了時間ロジックはver1.9/2.0のロジックを維持) ...
        total_seconds_in_minute_loop = (start_mm % 60) * 60 + start_ss
        
        spacer = ""
        if 0 <= start_fr <= 9:
            display_mm = (total_seconds_in_minute_loop // 60) % 60
            display_ss = total_seconds_in_minute_loop % 60
            formatted_start_time = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num)
            spacer = "　　　"
        elif 10 <= start_fr <= 22:
            display_mm = (total_seconds_in_minute_loop // 60) % 60
            display_ss = total_seconds_in_minute_loop % 60
            time_num_part = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num)
            formatted_start_time = f"{time_num_part}半"
            spacer = "　　"
        else:
            total_seconds_in_minute_loop += 1
            display_mm = (total_seconds_in_minute_loop // 60) % 60
            display_ss = total_seconds_in_minute_loop % 60
            formatted_start_time = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num)
            spacer = "　　　"

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
        
        if i + 1 < len(parsed_blocks):
            next_block = parsed_blocks[i+1]
            end_total_seconds = (end_hh * 3600) + (end_mm * 60) + end_ss + (end_fr / FRAME_RATE)
            next_start_total_seconds = (next_block['start_hh'] * 3600) + (next_block['start_mm'] * 60) + next_block['start_ss'] + (next_block['start_fr'] / FRAME_RATE)
            if next_start_total_seconds - end_total_seconds < CONNECTION_THRESHOLD:
                add_blank_line = False

        if add_blank_line:
            adj_ss = end_ss
            adj_mm = end_mm

            if 0 <= end_fr <= 9:
                adj_ss = end_ss - 1
                if adj_ss < 0:
                    adj_ss = 59
                    adj_mm -= 1
            
            adj_mm_display = adj_mm % 60
            
            if start_hh != end_hh or (start_mm % 60) != adj_mm_display:
                formatted_end_time = f"{adj_mm_display:02d}{adj_ss:02d}".translate(to_zenkaku_num)
            else:
                formatted_end_time = f"{adj_ss:02d}".translate(to_zenkaku_num)
                
            end_string = f" (~{formatted_end_time})"
            
        output_lines.append(f"{formatted_start_time}{spacer}{speaker_symbol}　{body}{end_string}")
        
        if add_blank_line and i < len(parsed_blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# （StreamlitのUI部分は変更なし）
# ... 省略 ...
st.set_page_config(page_title="Caption to Narration", page_icon="📝", layout="wide")
st.title('Caption to Narration')

st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)
col1, col2 = st.columns(2)

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
    
    input_text = st.text_area(
        "ナレーション原稿形式に変換します", 
        height=500, 
        placeholder="""キャプションをテキストで書き出した形式
00;00;00;00 - 00;00;02;29
N ああああ

xmlをサイトで変換した形式
００：００：１５：００　〜　００：００：１８：１３
N ああああ

この２つの形式に対応しています。ペーストして　Ctrl+Enter　を押して下さい
※混在も可能です

""",
        help=help_text
    )

with col2:
    st.header('')
    if input_text:
        try:
            converted_text = convert_narration_script(input_text)
            st.text_area("コピーしてお使いください", value=converted_text, height=500)
        except Exception as e:
            st.error(f"エラーが発生しました。テキストの形式を確認してください。\n\n詳細: {e}")

# --- フッターをカスタマイズ ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: right; font-size: 9px; color: #C5D6B9;">
        © 2025 kimika Inc. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
