import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(page_title="SPI語彙クイズ", layout="centered")
st.title("📝 SPI語彙クイズアプリ")

# 語彙データの読み込み
def load_data():
    df = pd.read_excel("頻出単語200選.xlsx", sheet_name="頻出語句一覧")
    df = df[["単語", "単語の意味", "読み方"]].copy()
    df["正解数"] = 0
    df["不正解数"] = 0
    df["自信なし"] = 0
    return df

# 出題語彙の選択（重み付きランダム）
def select_question(df):
    weights = []
    for _, row in df.iterrows():
        weight = 1 + row["不正解数"] - 0.5 * row["正解数"]
        weight = max(weight, 0.1)
        weights.append(weight)
    selected_index = random.choices(range(len(df)), weights=weights, k=1)[0]
    return selected_index, df.iloc[selected_index]

# 選択肢の作成（正解＋他の選択肢）
def generate_choices(df, correct_meaning):
    other_meanings = df["単語の意味"].tolist()
    other_meanings = [m for m in other_meanings if m != correct_meaning]
    choices = random.sample(other_meanings, 4) + [correct_meaning]
    random.shuffle(choices)
    return choices

# データ保存
def save_progress(df):
    df.to_csv("progress.csv", index=False)

def load_progress():
    if os.path.exists("progress.csv"):
        df = pd.read_csv("progress.csv")
        if "自信なし" not in df.columns:
            df["自信なし"] = 0
        return df
    return load_data()

# データ読み込み
df = load_progress()

# 統計表示（右上）
with st.container():
    total = len(df)
    unanswered = df[(df["正解数"] == 0) & (df["不正解数"] == 0)].shape[0]
    answered = df[(df["正解数"] > 0) | (df["不正解数"] > 0)].shape[0]
    mistakes = df[df["不正解数"] > 0].shape[0]
    st.markdown(f"""
    <div style='text-align:right;'>
        <strong>未回答：</strong> {unanswered}
        <strong>回答済み：</strong> {answered}
        <strong>間違い：</strong> {mistakes}
    </div>
    """, unsafe_allow_html=True)

# 出題処理
if "question_index" not in st.session_state:
    st.session_state.question_index, st.session_state.current_row = select_question(df)
    st.session_state.choices = generate_choices(df, st.session_state.current_row["単語の意味"])
    st.session_state.answered = False
    st.session_state.unsure = False  # チェック初期化

word = st.session_state.current_row["単語"]
yomi = st.session_state.current_row["読み方"]
choices = st.session_state.choices
answer = st.radio(f"この単語の意味は？ → **{word}**", choices, key="answer")
unsure = st.checkbox("合っているか自信がない", key="unsure", value=False)

if not st.session_state.answered:
    if st.button("回答する"):
        correct = st.session_state.current_row["単語の意味"]
        idx = st.session_state.question_index
        if answer == correct:
            st.success("正解！")
        else:
            st.error(f"不正解… 正解は「{correct}」")
        st.info(f"この単語の読み方：**{yomi}**")
        if answer == correct:
            df.at[idx, "正解数"] += 1
        else:
            df.at[idx, "不正解数"] += 1
        if unsure:
            df.at[idx, "自信なし"] += 1
        save_progress(df)
        st.session_state.answered = True

if st.session_state.answered:
    if st.button("次の問題に進む"):
        del st.session_state.question_index
        del st.session_state.current_row
        del st.session_state.choices
        del st.session_state.answered
        del st.session_state.unsure
        st.rerun()

st.markdown("---")
if st.button("間違えた問題だけ復習するモードへ切り替え"):
    st.switch_page("pages/wrong.py")
