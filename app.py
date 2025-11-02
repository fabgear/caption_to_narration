import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- 【バグ修正・最終完成版】▼▼▼
# ===============================================================
def convert_narration_script(text):
    # --- 変換テーブルの準備 ---
    to_zenkaku_num = str.maketrans('0123456789', '０１２３４５６７８９')
    hankaku_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
    zenkaku_chars = 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９　'
    to_zenkaku_all = str.maketrans(hankaku_chars, zenkaku_chars)
    to_hankaku_time = str.maketrans('０１２３４５６７８９：〜', '0123456789:~')

    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    start_index = -1
    time_pattern = r'(\d{2}):(\d{2}):(\d{2})(?:[.;](\d{2}))?\s*-\s*(\d{2}):(\d{2}):(\d{2})(?:[.;](\d{2}))?'
    
    for i, line in enumerate(lines):
        normalized_line = line.translate(to_hankaku_time).replace('~', '-')
        if re.match(time_pattern, normalized_line):
            start_index = i
            break
            
    if start_index == -1:
        return "エラー：変換可能なタイムコードが見つかりませんでした。"
        
    relevant_lines = lines[start_index:]

    blocks = []
    for i in range(0, len(relevant_lines), 2):
        if i + 1 < len(relevant_lines):
            blocks.append({'time': relevant_lines[i], 'text': relevant_lines[i+1]})

    output_lines = []
    for i, block in enumerate(blocks):
        normalized_time_str = block['time'].translate(to_hankaku_time).replace('~', '-')
        time_match = re.match(time_pattern, normalized_time_str)
        if not time_match: continue
        
        groups = time_match.groups()
        # --- ▼▼▼【バグ修正】ここで8個の変数を正しく受け取るように修正しました ▼▼▼ ---
        start_hh, start_mm, start_ss, start_dec, end_hh, end_mm, end_ss, end_dec = [int(g or 0) for g in groups]

        # 1. 開始時間のフォーマット（hhを考慮）
        start_total_seconds = start_ss + start_dec / 100.0
        rounded_sec = round(start_total_seconds)
        if rounded_sec >= 60:
            start_mm += 1
            rounded_sec = 0
            if start_mm >= 60:
                start_hh += 1
                start_mm = 0
        
        if start_hh > 0:
            formatted_start_time = f"{start_hh:02d}{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku_num)
        else:
            formatted_start_time = f"{start_mm:02d}{rounded_sec:02d}".translate(to_zenkaku_num)

        # 2. 話者記号と本文のフォーマット
        speaker_symbol = 'Ｎ'
        text_content = block['text'].strip()
        body = ""

        if text_content == "無記載":
            body = ""
        else:
            match = re.match(r'^(\S+)\s+(.*)', text_content)
            if match:
                raw_speaker = match.group(1)
                body = match.group(2).strip()
                if raw_speaker.upper() == 'N':
                    speaker_symbol = 'Ｎ'
                else:
                    speaker_symbol = raw_speaker.translate(to_zenkaku_all)
            else:
                if text_content.startswith('Ｎ '): body = text_content[2:].strip()
                elif text_content.startswith('N '): body = text_content[2:].strip()
                else: body = text_content

        if not body:
            body = "※注意！本文なし！"
        
        body = body.translate(to_zenkaku_all)
        
        # 3. 終了時間と空白行の処理
        end_string = ""
        add_blank_line = True

        if i + 1 < len(blocks):
            next_normalized_time = blocks[i+1]['time'].translate(to_hankaku_time).replace('~', '-')
            next_time_match = re.match(time_pattern, next_normalized_time)
            if next_time_match:
                next_groups = next_time_match.groups()
                next_start_hh, next_start_mm, next_start_ss, next_start_dec, _, _, _, _ = [int(g or 0) for g in next_groups]
                end_total_seconds = (end_hh * 3600) + (end_mm * 60) + end_ss + (end_dec / 100.0)
                next_start_total_seconds = (next_start_hh * 3600) + (next_start_mm * 60) + next_start_ss + (next_start_dec / 100.0)
                if next_start_total_seconds - end_total_seconds < 1.0:
                    add_blank_line = False

        if add_blank_line:
            if start_hh != end_hh:
                formatted_end_time = f"{end_hh:02d}{end_mm:02d}{end_ss:02d}".translate(to_zenkaku_num)
            elif start_mm != end_mm:
                formatted_end_time = f"{end_mm:02d}{end_ss:02d}".translate(to_zenkaku_num)
            else:
                formatted_end_time = f"{end_ss:02d}".translate(to_zenkaku_num)
            end_string = f"　（～{formatted_end_time}）"
            
        # 4. 最終的な行を組み立て
        output_lines.append(f"{formatted_start_time}　　{speaker_symbol}　{body}{end_string}")
        if add_blank_line and i < len(blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# ===============================================================
# ▼▼▼ Streamlitの画面を作る部分（変更なし）▼▼▼
# ===============================================================
st.set_page_config(
    page_title="Caption to Narration",
    page_icon="📝",
    layout="wide"
)
st.title('Caption to Narration')

st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.header('')
    input_text = st.text_area(
        "Premiereで書き出したキャプションをペーストして [Ctrl+Enter] ", 
        height=500, 
        placeholder="""例：
シーケンス 01

00;00;00;00 - 00;00;02;29
N ああああ

または、
００：００：１５　〜　００：００：１８
無記載

上のどちらの形式でも、下のように変換されます。
------------------------------------------------
００００　　Ｎ　ああああ　（～０２）

００１５　　Ｎ　※注意！本文なし！　（～１８）
------------------------------------------------
【話者名のルール】
・行頭に「N」や「n」があれば「Ｎ」になります。
・行頭に「VO」や「木村」などがあれば、それが話者名になります。
・話者名がない場合は、自動で「Ｎ」が補われます。
・「無記載」と書かれた行は、本文なしとして扱います。

【その他の機能】
・先頭のシーケンス名や余分な改行は自動で無視します。
・１時間を超えるタイムコード（hh:mm:ss）にも対応しています。
"""
    )

with col2:
    st.header('')
    if input_text:
        try:
            converted_text = convert_narration_script(input_text)
            st.text_area("コピーしてお使いください", value=converted_text, height=500)
        except Exception as e:
            st.error(f"エラーが発生しました。テキストの形式を確認してください。\n\n詳細: {e}")
