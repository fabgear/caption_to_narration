import streamlit as st
import re
import math

# ===============================================================
# ▼▼▼ ツールの本体（エンジン部分）- 【Ver.2：N強制挿入オプション対応】▼▼▼
# ===============================================================
# --- ▼▼▼【変更点1】関数の引数に、チェックボックスの状態を受け取る変数を追加 ▼▼▼ ---
def convert_narration_script(text, force_n_insertion):
    # --- 変換テーブルの準備 ---
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

        # --- ▼▼▼【変更点2】ここから話者名判定ロジックを修正 ▼▼▼ ---
        speaker_symbol = None  # いったん「なし」で初期化
        text_content = block['text']
        body = ""

        match = re.match(r'^(\S+)\s+(.*)', text_content)
        if match:
            # "VO あああ" のように、話者名らしきものがある場合
            raw_speaker = match.group(1); body = match.group(2).strip()
            if raw_speaker.upper() == 'N': speaker_symbol = 'Ｎ'
            else: speaker_symbol = raw_speaker.translate(to_zenkaku_all)
        else:
            # 話者名らしきものがなく、本文だけの場合
            body = text_content.strip()
            if body.upper() == 'N' or body == 'Ｎ': body = ""

        # チェックボックスがオンで、かつ話者名が見つからなかった場合のみ、Nを補う
        if force_n_insertion and speaker_symbol is None:
            speaker_symbol = 'Ｎ'

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
        
        # --- ▼▼▼【変更点3】最終的な出力行の組み立て方を修正 ▼▼▼ ---
        if speaker_symbol:
            # 話者名がある場合 (チェックあり、または元々VOなどがあった)
            output_lines.append(f"{formatted_start_time}　　{speaker_symbol}　{body}{end_string}")
        else:
            # 話者名がない場合 (チェックなし)
            output_lines.append(f"{formatted_start_time}　　{body}{end_string}")

        if add_blank_line and i < len(blocks) - 1:
            output_lines.append("")
            
    return "\n".join(output_lines)

# ===============================================================
# ▼▼▼ Streamlitの画面を作る部分 - 【Ver.2：チェックボックス追加】▼▼▼
# ===============================================================
st.set_page_config(page_title="Caption to Narration", page_icon="📝", layout="wide")
st.title('Caption to Narration')

st.markdown("""<style> textarea::placeholder { font-size: 13px; } </style>""", unsafe_allow_html=True)

# --- ▼▼▼【変更点4】タイトルとチェックボックスを横並びに配置 ▼▼▼ ---
title_col, checkbox_col = st.columns([0.8, 0.2]) # 横幅の比率を調整
with title_col:
    st.subheader("1. 元のテキストを貼り付け")
    st.caption("Premiere Proから書き出したキャプションテキストを、そのまま貼り付けてください。")
with checkbox_col:
    # `value=True`で、デフォルトでチェックが入った状態にする
    force_n_insertion = st.checkbox("N強制挿入", value=True, help="話者名がない行に、自動で「Ｎ」を補います。")


col1, col2 = st.columns(2)

help_text = """
**Premiere Proから書き出された、様々な形式のキャプションテキストに対応しています。**

---
**【対応しているタイムコード形式】**
・`00;00;00;00 - 00;00;02;29` (セミコロン区切り)
・`００：００：００ 〜 ００：００：３０` (全角、チルダ区切り)
・ミリ秒の有無、区切り文字の種類を自動で判別します。

---
**【話者名のルール】**
・**N** または **n** → **Ｎ**
・**VO**、**木村** など → **ＶＯ**、**木村** (そのまま話者名として認識)
・話者名なし → **Ｎ** (「N強制挿入」がオンの場合)

---
**【その他の機能】**
・本文が空の場合は「※注意！本文なし！」と表示します。
・先頭のシーケンス名や余分な改行は自動で無視します。
・１時間を超えるタイムコードにも完全対応しています。
・本文中の半角英数字は、すべて全角に変換されます。
"""

with col1:
    input_text = st.text_area(
        "ここにテキストを貼り付けてください",
        height=500, 
        placeholder="ここにテキストを貼り付けてください",
        help=help_text,
        label_visibility="collapsed"
    )

with col2:
    st.subheader("2. 変換結果をコピー")
    st.caption("変換されたテキストをコピーして、ナレーション原稿としてお使いください。")

    if input_text:
        try:
            # --- ▼▼▼【変更点5】チェックボックスの状態を関数に渡す ▼▼▼ ---
            converted_text = convert_narration_script(input_text, force_n_insertion)
            st.text_area(
                "ここに変換結果が表示されます",
                value=converted_text, 
                height=500,
                label_visibility="collapsed"
            )
        except Exception as e:
            st.error(f"エラーが発生しました。テキストの形式を確認してください。\n\n詳細: {e}")

# --- フッター（コピーライト表記）は変更なし ---
st.markdown("---")
st.caption("Created by kimika Inc.")
