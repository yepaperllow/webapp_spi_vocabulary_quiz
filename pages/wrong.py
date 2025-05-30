import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="復習モード", layout="wide")
st.title("🔁 復習モード（間違えた問題のみ）")

# 保存された進捗データを読み込み
def load_progress():
    if os.path.exists("progress.csv"):
        return pd.read_csv("progress.csv")
    st.warning("進捗データが見つかりません。まずは通常モードで問題に取り組んでください。")
    st.stop()

df = load_progress()
if "自信なし" not in df.columns:
    df["自信なし"] = 0

# 統計表示
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

st.markdown("---")

# 間違えた語彙一覧表示モード（不正解数が一度でも1以上あったもの）
if st.checkbox("間違えた語彙一覧を表示"):
    history_mistakes = df[df["正解数"] + df["不正解数"] > 0]  # 回答済みの中から
    history_mistakes = history_mistakes[history_mistakes["不正解数"] > 0]  # 一度でも間違えたことのあるもの
    history_mistakes = history_mistakes[["単語", "読み方", "単語の意味"]].drop_duplicates()
    st.dataframe(history_mistakes.reset_index(drop=True))
    st.stop()

# 自信のなかった語彙一覧表示モード
if st.checkbox("合っているか自信がなかった語彙一覧を表示"):
    unsure_df = df[df["自信なし"] > 0][["単語", "読み方", "単語の意味"]].drop_duplicates()
    st.dataframe(unsure_df.reset_index(drop=True))
    st.stop()

# ▼ 以下、出題モード
# 不正解が1回以上ある問題だけを対象に
mistake_df = df[df["不正解数"] > 0].copy()

if mistake_df.empty:
    st.success("間違えた問題はありません！")
    st.stop()

# 出題と状態の初期化
if "review_question" not in st.session_state:
    selected_row = mistake_df.sample(1).iloc[0]
    st.session_state.review_question = selected_row
    correct_meaning = selected_row["単語の意味"]
    other_meanings = df["単語の意味"].tolist()
    other_meanings = [m for m in other_meanings if m != correct_meaning]
    choices = random.sample(other_meanings, 4) + [correct_meaning]
    random.shuffle(choices)
    st.session_state.review_choices = choices
    st.session_state.review_answered = False
    st.session_state.review_unsure = False  # 自信なし状態の初期化

selected_row = st.session_state.review_question
word = selected_row["単語"]
yomi = selected_row.get("読み方", "（読み方情報なし）")
correct_meaning = selected_row["単語の意味"]
choices = st.session_state.review_choices

# UI表示
answer = st.radio(f"この単語の意味は？ → **{word}**", choices, key="review_answer")
unsure = st.checkbox("合っているか自信がない", key="review_unsure", value=False)

if not st.session_state.review_answered:
    if st.button("回答する"):
        idx = df.index[(df["単語"] == word) & (df["単語の意味"] == correct_meaning)][0]
        if answer == correct_meaning:
            st.success("正解！")
            df.at[idx, "正解数"] += 1
            df.at[idx, "不正解数"] = max(df.at[idx, "不正解数"] - 1, 0)
        else:
            st.error(f"不正解… 正解は「{correct_meaning}」")
            df.at[idx, "不正解数"] += 1
        if unsure:
            df.at[idx, "自信なし"] += 1
        st.info(f"この単語の読み方：**{yomi}**")
        df.to_csv("progress.csv", index=False)
        st.session_state.review_answered = True

if st.session_state.review_answered:
    if st.button("次の問題に進む"):
        del st.session_state.review_question
        del st.session_state.review_choices
        del st.session_state.review_answered
        del st.session_state.review_unsure
        st.rerun()