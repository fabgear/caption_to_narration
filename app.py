import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- （ver3.7：N強制挿入ロジック追加）▼▼▼
# ===============================================================
# N_FORCE_INSERT_FLAG を受け取るように変更
def convert_narration_script(text, n_force_insert_flag=True):
    # （中略：設定値とmaketrnas定義はver2を維持）
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

        # ▼▼▼【ver3.7 N強制挿入ロジック】if文をフラグで制御 ▼▼▼
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
            # N強制挿入がOFFの場合: 話者/本文の処理を一切行わず、そのまま出力
            speaker_symbol = ''; body = text_content 
        # ▲▲▲【ver3.7 N強制挿入ロジック】ここまで ▼▼▼

        body = body.translate(to_zenkaku_all)
        
        # （中略：終了時間とつながり判定ロジックは変更なし）
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
            
        output_lines.append(f"{formatted_start_time}{spacer}{speaker_symbol}　{body}{end_string}")
        
        if add_blank_line and i < len(parsed_blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)


# ===============================================================
# ▼▼▼ Streamlitの画面を作る部分 - （ver3.7：多段カラムの安定版）▼▼▼
# ===============================================================
st.set_page_config(page_title="Caption to Narration", page_icon="📝", layout="wide")
st.title('Caption to Narration')

st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)

# ヘルプテキストを定義（変更なし）
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
# 1段目：メインのテキストエリアとタイトル
# ----------------------------------------------------------------------------------
col1_top, col2_top = st.columns(2)

# タイトルはテキストエリアと同一カラムの最上部に配置 (ver2構造)
with col1_top:
    st.header('ナレーション原稿形式に変換します')
with col2_top:
    st.header('コピーしてお使いください')

# テキストエリアの定義は次のブロックで行うため、ここでは st.empty() でプレースホルダーを確保
# st.text_areaの戻り値はここで定義する必要があるため、構造を単純化します。
with col1_top:
    input_text = st.text_area(
        "　", 
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

with col2_top:
    output_text_area = st.empty()


# ----------------------------------------------------------------------------------
# 2段目：コントロールエリア（左右バランスを崩さない新しい領域）
# ----------------------------------------------------------------------------------
col1_bottom, col2_bottom = st.columns(2)

# ▼▼▼【ver3.7 変更点】N強制挿入チェックボックスを2段目の左に配置 ▼▼▼
with col1_bottom:
    n_force_insert = st.checkbox("N強制挿入", value=True)

with col2_bottom:
    # 右下エリアは空で、左のチェックボックスに合わせた高さ調整の役割
    # 上部エリアとの間に間隔を開けるために st.markdown を使用
    st.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True) # チェックボックスとだいたい同じ高さ


# ----------------------------------------------------------------------------------
# 3. 変換結果の表示（メインロジック）
# ----------------------------------------------------------------------------------
if input_text:
    try:
        # チェックボックスの状態を反映させて変換を一度行う
        converted_text = convert_narration_script(input_text, n_force_insert)
        
        # プレースホルダーに結果を表示
        with col2_top:
             st.text_area("　", value=converted_text, height=500)
             
    except Exception as e:
        # エラー時
        with col2_top:
            st.text_area("　", value="エラーが発生しました。テキストの形式を確認してください。", height=500)
            st.error(f"詳細: {e}")
else:
    # 入力がない初期状態の場合、右側を空にしてバランスを保つ
    with col2_top:
        st.text_area("　", value="", height=500)

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
