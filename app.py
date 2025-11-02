import streamlit as st
import re
import math
# ▼▼▼【ver4.3 変更点】外部ライブラリのインポート ▼▼▼
from streamlit_extras.clipboard import copy_to_clipboard 

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- （ver4.3：ロジック変更なし）▼▼▼
# ===============================================================
# N_FORCE_INSERT_FLAG を受け取るように変更
def convert_narration_script(text, n_force_insert_flag=True):
    # （中略：ロジックはver3と同一。機能は実装済み）
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

    previous_end_hh = -1

    for i, block in enumerate(parsed_blocks):
        start_hh, start_mm, start_ss, start_fr = block['start_hh'], block['start_mm'], block['start_ss'], block['start_fr']
        end_hh, end_mm, end_ss, end_fr = block['end_hh'], block['end_mm'], block['end_ss'], block['end_fr']

        should_insert_h_marker = False
        marker_hh_to_display = -1
        
        if i == 0:
            if start_hh > 0: should_insert_h_marker = True; marker_hh_to_display = start_hh
            previous_end_hh = end_hh 
        else:
            if start_hh < end_hh: should_insert_h_marker = True; marker_hh_to_display = end_hh 
            elif start_hh > previous_end_hh: should_insert_h_marker = True; marker_hh_to_display = start_hh 

        if should_insert_h_marker:
             output_lines.append("")
             output_lines.append(f"【{str(marker_hh_to_display).translate(to_zenkaku_num)}Ｈ】")
             output_lines.append("")
             
        previous_end_hh = end_hh 

        total_seconds_in_minute_loop = (start_mm % 60) * 60 + start_ss
        spacer = ""
        if 0 <= start_fr <= 9:
            display_mm = (total_seconds_in_minute_loop // 60) % 60; display_ss = total_seconds_in_minute_loop % 60
            formatted_start_time = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num); spacer = "　　　"
        elif 10 <= start_fr <= 22:
            display_mm = (total_seconds_in_minute_loop // 60) % 60; display_ss = total_seconds_in_minute_loop % 60
            time_num_part = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num); formatted_start_time = f"{time_num_part}半"; spacer = "　　"
        else:
            total_seconds_in_minute_loop += 1
            display_mm = (total_seconds_in_minute_loop // 60) % 60; display_ss = total_seconds_in_minute_loop % 60
            formatted_start_time = f"{display_mm:02d}{display_ss:02d}".translate(to_zenkaku_num); spacer = "　　　"

        speaker_symbol = 'Ｎ'
        text_content = block['text']
        body = ""

        if n_force_insert_flag:
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
        else:
            speaker_symbol = '' # 話者記号は空
            body = text_content # 元のテキスト全体を本文として扱う
            
            # 本文が空（または空白のみ）の場合、警告を出す
            if not body.strip():
                body = "※注意！本文なし！"

        body = body.translate(to_zenkaku_all)
        
        end_string = ""; add_blank_line = True
        
        if i + 1 < len(parsed_blocks):
            next_block = parsed_blocks[i+1]
            end_total_seconds = (end_hh * 3600) + (end_mm * 60) + end_ss + (end_fr / FRAME_RATE)
            next_start_total_seconds = (next_block['start_hh'] * 3600) + (next_block['start_mm'] * 60) + next_block['start_ss'] + (next_block['start_fr'] / FRAME_RATE)
            if next_start_total_seconds - end_total_seconds < CONNECTION_THRESHOLD:
                add_blank_line = False

        if add_blank_line:
            adj_ss = end_ss; adj_mm = end_mm
            if 0 <= end_fr <= 9: adj_ss = end_ss - 1; 
            if adj_ss < 0: adj_ss = 59; adj_mm -= 1
            
            adj_mm_display = adj_mm % 60
            
            if start_hh != end_hh or (start_mm % 60) != adj_mm_display:
                formatted_end_time = f"{adj_mm_display:02d}{adj_ss:02d}".translate(to_zenkaku_num)
            else:
                formatted_end_time = f"{adj_ss:02d}".translate(to_zenkaku_num)
                
            end_string = f" (～{formatted_end_time})"
            
        if n_force_insert_flag:
            output_lines.append(f"{formatted_start_time}{spacer}{speaker_symbol}　{body}{end_string}")
        else:
             output_lines.append(f"{formatted_start_time}{spacer}{body}{end_string}")

        if add_blank_line and i < len(parsed_blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# ===============================================================
# ▼▼▼ Streamlitの画面を作る部分 - （ver4.3：コピーボタン最終版）▼▼▼
# ===============================================================
st.set_page_config(page_title="Caption to Narration", page_icon="📝", layout="wide")
st.title('Caption to Narration')

# ▼▼▼【ver4.3 変更点】CSSを再定義（文字サイズのみ維持） ▼▼▼
st.markdown("""<style> 
textarea::placeholder { 
    font-size: 13px;
} 
textarea {
    font-size: 14px !important;
}
</style>""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

help_text = """
【機能詳細】  
・ENDタイム(秒のみ)が自動で入ります  
　分をまたぐ時は(分秒)、次のナレーションと繋がる時は割愛されます  
・頭の「N」は自動で全角に変換され未記載の時は自動挿入されます  
　VOや実況などN以外はそのまま適応されます  
・Hをまたぐときは自動で仕切りが入ります  
・ナレーション本文の半角英数字は全て全角に変換します  
"""

# ----------------------------------------------------------------------------------
# 1. 左カラム（入力）
# ----------------------------------------------------------------------------------
with col1:
    st.header('')
    
    input_text = st.text_area(
        "ナレーション原稿形式に変換します", 
        height=500, 
        placeholder="""①キャプションをテキストで書き出した形式
00;00;00;00 - 00;00;02;29
N ああああ

②xmlをサイトで変換した形式
００:００:１５　〜　００:００：１８
N ああああ

この２つの形式に対応しています。ペーストして　Ctrl+Enter　を押して下さい
①の方が細かい変換をするのでオススメです

""",
        help=help_text
    )
    
    n_force_insert = st.checkbox("N強制挿入", value=True)


# ----------------------------------------------------------------------------------
# 2. 右カラム（出力）
# ----------------------------------------------------------------------------------
with col2:
    st.header('')
    
    if input_text:
        try:
            converted_text = convert_narration_script(input_text, n_force_insert)
            
            # ▼▼▼【ver4.3 変更点】ヘッダーとボタンを同じ行に配置 ▼▼▼
            col_title, col_button = st.columns([0.6, 0.4]) # タイトルとボタンの幅を調整
            
            with col_title:
                st.markdown('### コピーしてお使いください') # ヘッダーより小さいMarkdownで余白を調整
            
            with col_button:
                # 外部ライブラリを使用した確実なコピーボタン
                # st.button のスタイルに近づけるため、st.button を使用
                if st.button("クリップボードにコピー", key="copy_btn", type="primary"):
                    # copy_to_clipboard は裏側で JavaScript を使ってクリップボードに書き込みます
                    copy_to_clipboard(converted_text) 
                    st.toast("テキストがコピーされました！")

            # 出力テキストエリア（左と同じ500pxに固定）
            st.text_area("　", value=converted_text, height=500)
            
            # 左のチェックボックスの高さ分、下の余白を確保し、フッターとの距離を揃える
            st.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.header('コピーしてお使いください')
            st.error(f"エラーが発生しました。テキストの形式を確認してください。\n\n詳細: {e}")
            # エラー時もテキストエリアとボタンの分の高さを確保
            st.markdown('<div style="height: 538px;"></div>', unsafe_allow_html=True) 
    else:
        # 入力がない場合、右側を完全に空にするが、高さは維持
        st.header('') # ヘッダー分の高さを確保
        st.markdown('<div style="height: 538px;"></div>', unsafe_allow_html=True) # テキストエリアとボタンの分の高さを確保


# --- フッターをカスタマイズ ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: right; font-size: 12px; color: #C5D6B9;">
        © 2025 kimika Inc. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
