import streamlit as st
import pandas as pd

# 画面の横幅を広く使う設定
st.set_page_config(layout="wide", page_title="総合資産ライフプランシミュレーター 完全版")

st.title("総合資産ライフプランシミュレーター【完全版】 📊")
st.write("現金・NISA・課税口座・iDeCoの運用から、老後の「物価上昇（インフレ）」と「指定額取り崩し」まで網羅した決定版")

# --- サイドバー：条件設定 ---
st.sidebar.header("👨‍💼 基本設定")
current_age = st.sidebar.number_input("現在の年齢（歳）", value=30, min_value=0, max_value=100, step=1)
years = st.sidebar.slider("シミュレーション期間（年間）", min_value=1, max_value=50, value=30)
rate = st.sidebar.number_input("投資の想定年利（％）", value=5.0, min_value=0.0, max_value=20.0, step=0.1)

st.sidebar.header("🏦 現在の資産内訳（初期値）")
init_cash_bal = st.sidebar.number_input("現在の現金残高（生活防衛資金など）（円）", value=0, step=100000)
init_nisa_bal = st.sidebar.number_input("現在のNISA/旧NISA残高（円）", value=0, step=100000)
init_nisa_used = st.sidebar.number_input("現在の新NISA・生涯枠使用額（元本累計）（円）", value=0, step=100000)
init_ideco_bal = st.sidebar.number_input("現在のiDeCo残高（円）", value=0, step=100000)
init_taxable_bal = st.sidebar.number_input("現在の課税口座（特定口座等）時価（円）", value=0, step=100000)
init_taxable_prin = st.sidebar.number_input("現在の課税口座の「投資元本」（円）", value=0, step=100000)

st.sidebar.header("💰 現役時代の積立設定")
nisa_annual = st.sidebar.number_input("NISA 年間積立希望額（円）", value=1200000, step=100000)
ideco_annual = st.sidebar.number_input("iDeCo 年間積立額（円）", value=276000, step=1000)
ideco_end_age = st.sidebar.number_input("iDeCo 積立終了年齢（歳）", value=60, min_value=20, max_value=65, step=1)

st.sidebar.header("👴 老後の取り崩し設定（新機能）")
withdraw_start_age = st.sidebar.number_input("取り崩し（リタイア）開始年齢（歳）", value=65, min_value=20, max_value=100, step=1)
withdraw_annual = st.sidebar.number_input("老後の年間取り崩し希望額（生活費）（円）", value=1800000, step=100000)

st.sidebar.header("⚖️ 税金・インフレ対策")
tax_rate = st.sidebar.number_input("課税口座の将来税率（％）", value=20.315, min_value=0.0, max_value=50.0, step=0.5)
inflation_rate = st.sidebar.number_input("想定インフレ率（物価上昇率）（％）", value=1.5, min_value=0.0, max_value=10.0, step=0.1)
nisa_limit = st.sidebar.number_input("NISA 生涯投資枠の上限（円）", value=18000000, step=1000000)
ideco_tax_age = st.sidebar.number_input("iDeCo 受取・課税年齢（歳）", value=65, min_value=60, max_value=75, step=1)
ideco_tax_rate = st.sidebar.number_input("iDeCo 受取時の想定実質税率（％）", value=10.0, min_value=0.0, max_value=50.0, step=0.5)

st.sidebar.header("🛡️ 年金・臨時収支設定")
pension_start_age = st.sidebar.number_input("年金 受給開始年齢（歳）", value=65, min_value=60, max_value=75, step=1)
pension_annual = st.sidebar.number_input("年金 受給年額（円）", value=1200000, step=100000)
insurance_payout_age = st.sidebar.number_input("保険満期金・臨時収入の年齢（歳）", value=60, min_value=0, max_value=100, step=1)
insurance_payout = st.sidebar.number_input("保険満期金・臨時収入の額（円）", value=0, step=100000)
annual_expense = st.sidebar.number_input("毎年のその他固定支出（円）", value=0, step=10000)


# --- 計算ロジック ---
cash_bal = init_cash_bal
nisa_bal = init_nisa_bal
nisa_used = init_nisa_used
ideco_bal = init_ideco_bal
taxable_bal = init_taxable_bal
taxable_prin = init_taxable_prin

data = []
katsu_age = None  # 資産枯渇年齢の記録用

for year in range(1, years + 1):
    age = current_age + year
    is_retired = (age >= withdraw_start_age)
    
    # 1. 毎年の投資・積立処理（取り崩し開始年齢以降は積立を自動ストップ）
    current_nisa_in = 0
    current_taxable_in = 0
    
    if not is_retired:
        if age <= ideco_end_age:
            ideco_bal += ideco_annual
        
        nisa_space = max(0, nisa_limit - nisa_used)
        if nisa_space >= nisa_annual:
            current_nisa_in = nisa_annual
            nisa_used += current_nisa_in
        elif nisa_space > 0:
            current_nisa_in = nisa_space
            current_taxable_in = nisa_annual - nisa_space
            nisa_used += current_nisa_in
        else:
            current_taxable_in = nisa_annual
            
        nisa_bal += current_nisa_in
        taxable_bal += current_taxable_in
        taxable_prin += current_taxable_in
    
    # 2. 収入・支出・取り崩しのキャッシュフロー計算
    payout = insurance_payout if age == insurance_payout_age else 0
    pension = pension_annual if age >= pension_start_age else 0
    
    ideco_payout = 0
    if age == ideco_tax_age:
        ideco_tax = ideco_bal * (ideco_tax_rate / 100)
        ideco_payout = ideco_bal - ideco_tax
        ideco_bal = 0
        
    # 支出＝固定支出 ＋（取り崩し開始後は「取り崩し希望額」が生活費支出となる）
    current_expense = annual_expense + (withdraw_annual if is_retired else 0)
    
    net_cf = payout + pension + ideco_payout - current_expense
    cash_bal += net_cf
    
    # 現金がマイナス（不足）になった場合、投資口座から自動売却して補填
    if cash_bal < 0:
        shortfall = -cash_bal
        cash_bal = 0
        
        # 課税口座から取り崩し
        profit_ratio = max(0.0, (taxable_bal - taxable_prin) / taxable_bal) if taxable_bal > 0 else 0.0
        t_rate = tax_rate / 100
        denom = (1 - profit_ratio * t_rate)
        
        if denom > 0 and taxable_bal >= (shortfall / denom):
            withdraw_total = shortfall / denom
            taxable_bal -= withdraw_total
            taxable_prin -= withdraw_total * (1 - profit_ratio)
            shortfall = 0
        else:
            if taxable_bal > 0:
                actual_profit = max(0.0, taxable_bal - taxable_prin)
                net_withdraw = taxable_bal - (actual_profit * t_rate)
                shortfall -= net_withdraw
                taxable_bal = 0
                taxable_prin = 0
            
            # NISAから取り崩し
            if nisa_bal >= shortfall:
                nisa_bal -= shortfall
                shortfall = 0
            else:
                shortfall -= nisa_bal
                nisa_bal = 0
                
        # 投資全売却でも足りない場合は現金がマイナス（資産枯渇・赤字）
        if shortfall > 0:
            cash_bal = -shortfall
    
    # 3. 運用益の計算（現金にはつかない）
    nisa_profit = nisa_bal * (rate / 100)
    nisa_bal += nisa_profit
    
    if ideco_bal > 0:
        ideco_profit = ideco_bal * (rate / 100)
        ideco_bal += ideco_profit
        
    taxable_profit = taxable_bal * (rate / 100)
    taxable_bal += taxable_profit
    
    # 4. 現在の税引後価値と「インフレ調整後実質価値」の計算
    current_taxable_profit = max(0.0, taxable_bal - taxable_prin)
    taxable_net_val = taxable_bal - (current_taxable_profit * (tax_rate / 100))
    total_net_asset = cash_bal + nisa_bal + ideco_bal + taxable_net_val
    
    # インフレ調整（物価上昇分、将来の価値を今の価値に目減りさせる計算）
    real_total_net_asset = total_net_asset / ((1 + inflation_rate / 100) ** year)
    
    # 初めて資産が0以下になった年齢を記録
    if total_net_asset <= 0 and katsu_age is None:
        katsu_age = f"{age}歳"
    
    data.append({
        "年齢": f"{age}歳",
        "現金残高": int(cash_bal),
        "NISA残高": int(nisa_bal),
        "iDeCo残高": int(ideco_bal),
        "課税口座(税引後手取)": int(taxable_net_val),
        "実質総資産(額面)": int(total_net_asset),
        "実質総資産(インフレ調整後)": int(real_total_net_asset)
    })

df = pd.DataFrame(data)

# --- 画面表示（メインエリア） ---
col1, col2 = st.columns([2, 1])

with col1:
    # タブを使ってグラフをすっきり切り替えられるようにする
    tab1, tab2 = st.tabs(["📈 口座別の資産推移（額面）", "⚖️ インフレによる購買力への影響"])
    
    with tab1:
        st.subheader("口座別の資産推移（税引後・額面ベース）")
        chart_data = df.set_index("年齢")[["現金残高", "NISA残高", "iDeCo残高", "課税口座(税引後手取)"]]
        st.area_chart(chart_data)
        
    with tab2:
        st.subheader("額面上の金額 vs 物価上昇を考慮した「実質の価値」")
        st.write("インフレ率の分だけ、将来の同じ1,000万円でも買えるモノが減るリスクを視覚化しています。")
        chart_data_inflation = df.set_index("年齢")[["実質総資産(額面)", "実質総資産(インフレ調整後)"]]
        st.line_chart(chart_data_inflation)

with col2:
    st.subheader("💡 シミュレーション結果の要約")
    final_row = df.iloc[-1]
    
    # 資産枯渇の自動判定メッセージ
    if katsu_age:
        st.error(f"⚠️ 警告: 【{katsu_age}】時点で資産が枯渇（0円以下）します。取り崩し額を減らすか、現役時代の積立額を増やすシミュレーションをお試しください。")
    else:
        st.success(f"🎉 優秀: シミュレーション期間中、資産が尽きることはありません！")
        
    st.metric(label=f"{final_row['年齢']}時点の総資産（額面）", value=f"¥{final_row['実質総資産(額面)']:,}")
    st.metric(label=f"同時点の「今の物価に換算した」実質価値", value=f"¥{final_row['実質総資産(インフレ調整後)']:,}")
    
    # 【新機能】Excel/CSVダウンロードボタン（日本語文字化け対策BOM付き）
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📊 詳細データをCSV(Excel対応)で保存",
        data=csv_data,
        file_name='asset_simulation_result.csv',
        mime='text/csv',
    )

st.subheader("📋 詳細データ一覧（1円単位）")
st.dataframe(df.style.format({
    "現金残高": "¥{:,}", "NISA残高": "¥{:,}", "iDeCo残高": "¥{:,}", 
    "課税口座(税引後手取)": "¥{:,}", "実質総資産(額面)": "¥{:,}", "実質総資産(インフレ調整後)": "¥{:,}"
}), use_container_width=True)

# --- 免責事項 ---
st.markdown("---")
st.caption("""
⚠️ **免責事項（ご利用上の注意）**
* 本シミュレーターは、入力された条件に基づいて機械的に試算を行うものであり、将来の運用成果や法律・税制の改正内容を保証または確約するものではありません。
* 実際の投資成果は、市場環境の変動や個人の状況により大きく異なる場合があります。
* 本ツールの利用によって生じた利益、不利益、損害、トラブル等について、開発者は一切の責任を負いません。実際の投資判断および資産管理は、必ずご自身の責任において行っていただきますようお願いいたします。
""")
