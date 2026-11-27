# -*- coding: utf-8 -*-
"""仓位止损计算核心（逻辑与原 tkinter 版一致，仅剥离界面）"""
import math


def fmt(x, nd=8):
    """格式化数字：去掉多余的0"""
    if x is None:
        return "—"
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return s if s else "0"


def calculate(direction, B, L, T, mode, loss_value, loss_is_amount, stop_price, target_total, invested_cost=None):
    """direction: 'long'/'short'; B买入价; L杠杆; T总资金
    mode: 'loss'(按亏损上限算止损位) / 'stop'(按止损价算亏损)
    loss_value: 亏损数值; loss_is_amount: True=亏损额,False=亏损百分比
    stop_price: mode='stop'时的止损价; target_total: 目标总资金(可选,None跳过)
    invested_cost: 本单投入的保证金；None 表示使用全部总资金
    返回 dict: ok, lines(结果行列表), warnings(警告列表)
    """
    lines, warns = [], []
    cost = T if invested_cost is None else invested_cost
    if not math.isfinite(cost) or not 0 < cost <= T:
        return {"ok": False, "lines": [], "warnings": ["投入成本必须大于0且不能超过总资金"]}
    V = cost * L                 # 持仓市值
    qty = V / B                  # 持仓数量
    if direction == "long":
        liq = B * (1 - 1 / L)    # 爆仓价
    else:
        liq = B * (1 + 1 / L)

    lines.append(f"投入成本：{fmt(cost)}")
    lines.append(f"持仓市值：{fmt(V)}")
    lines.append(f"持仓数量：{fmt(qty)}")
    lines.append(f"爆仓价（约）：{fmt(liq)}")

    if mode == "loss":
        D = loss_value if loss_is_amount else loss_value / 100.0 * T
        if D <= 0:
            return {"ok": False, "lines": [], "warnings": ["亏损上限必须大于0"]}
        if D >= cost:
            return {"ok": False, "lines": [], "warnings": [
                f"亏损上限已达到或超过投入成本（{fmt(cost)}），按估算会先触发强平或与止损同时触发"]}

        x = D / V
        S = B * (1 - x) if direction == "long" else B * (1 + x)
        lines.append(f"止损价：{fmt(S)}")
        lines.append(f"价格回撤幅度：{fmt(x * 100, 4)}%")
        lines.append(f"触发止损时总资金：{fmt(T - D, 2)}")
        if x > 0.8 / L:
            warns.append("止损位已进入爆仓价80%区间，离强平很近，建议调低亏损上限")
    else:
        S = stop_price
        if direction == "long":
            if S >= B:
                return {"ok": False, "lines": [], "warnings": ["做多止损价应低于买入价"]}
            x = (B - S) / B
        else:
            if S <= B:
                return {"ok": False, "lines": [], "warnings": ["做空止损价应高于买入价"]}
            x = (S - B) / B
        if (direction == "long" and S <= liq) or (direction == "short" and S >= liq):
            warns.append("该止损价在爆仓价之后（或正好压线），实际会先爆仓，止损失效！")
        loss = V * x
        lines.append(f"价格回撤幅度：{fmt(x * 100, 4)}%")
        lines.append(f"该止损价的总亏损：{fmt(loss, 2)}")
        lines.append(f"触发止损时总资金：{fmt(T - loss, 2)}")
        lines.append(f"占总资金比例：{fmt(loss / T * 100, 2)}%")

    if target_total is not None and target_total > 0:
        profit = target_total - T
        x_tp = profit / V
        tp = B * (1 + x_tp) if direction == "long" else B * (1 - x_tp)
        if x_tp <= 0:
            warns.append("目标总资金未超过当前资金，无需开仓止盈")
        else:
            lines.append(f"目标总资金 {fmt(target_total, 2)} → 止盈价：{fmt(tp)}")

    return {"ok": True, "lines": lines, "warnings": warns}
