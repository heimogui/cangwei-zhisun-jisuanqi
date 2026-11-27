# -*- coding: utf-8 -*-
"""仓位止损计算器（合约）- Kivy 手机版，计算逻辑见 calc.py"""
import math
import os

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from calc import calculate

# Kivy 自带字体不含中文，按顺序找系统里的中文字体（Android / Windows / macOS）
FONT_CANDIDATES = [
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/NotoSansSC-Regular.otf",
    "/system/fonts/NotoSansSC-Regular.ttf",
    "/system/fonts/DroidSansFallback.ttf",
    "/system/fonts/NotoSerifCJK-Regular.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT:
    LabelBase.register(name="Roboto", fn_regular=FONT)  # 覆盖默认字体


class StopLossApp(App):
    title = "仓位止损计算器"

    def build(self):
        Window.softinput_mode = "below_target"
        self.sel = {}      # 单选项当前值
        self.fields = {}   # 输入框
        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        self.toggle(box, "方向", "dir", [("做多", "long"), ("做空", "short")])
        self.toggle(box, "模式", "mode",
                    [("按亏损上限→算止损位", "loss"), ("按止损价→算亏损", "stop")], self.sync_mode)
        self.field(box, "买入价", "buy", "7.07")
        self.field(box, "杠杆倍数", "lev", "5")
        self.field(box, "总资金", "total", "4600")
        self.field(box, "投入成本（留空按总资金）", "cost")
        self.toggle(box, "亏损上限形式", "kind", [("亏损百分比%", "pct"), ("亏损额", "amt")])
        self.field(box, "亏损上限数值", "loss", "20")
        self.field(box, "止损价（按止损价模式用）", "stop")
        self.field(box, "目标总资金（可选，算止盈价）", "target")

        btn = Button(text="计 算", size_hint_y=None, height=dp(52))
        btn.bind(on_release=self.on_calc)
        box.add_widget(btn)

        self.result = Label(text="", size_hint_y=None, halign="left", valign="top")
        self.result.bind(
            width=lambda i, w: setattr(i, "text_size", (w, None)),
            texture_size=lambda i, s: setattr(i, "height", s[1] + dp(16)),
        )
        box.add_widget(self.result)

        scroll.add_widget(box)
        self.sync_mode()
        return scroll

    # ---------- 界面组件 ----------
    def caption(self, box, text):
        lb = Label(text=text, size_hint_y=None, height=dp(26), halign="left", valign="middle")
        lb.bind(size=lambda i, s: setattr(i, "text_size", s))
        box.add_widget(lb)

    def toggle(self, box, title, key, opts, cb=None):
        self.caption(box, title)
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.sel[key] = opts[0][1]
        for i, (text, val) in enumerate(opts):
            b = ToggleButton(text=text, group=key, allow_no_selection=False,
                             state="down" if i == 0 else "normal")
            b.bind(state=lambda inst, st, v=val: self.pick(key, v, st, cb))
            row.add_widget(b)
        box.add_widget(row)

    def pick(self, key, val, st, cb):
        if st == "down":
            self.sel[key] = val
            if cb:
                cb()

    def field(self, box, title, key, default=""):
        self.caption(box, title)
        ti = TextInput(text=default, multiline=False, input_filter="float",
                       size_hint_y=None, height=dp(44), write_tab=False)
        box.add_widget(ti)
        self.fields[key] = ti

    def sync_mode(self, *_):
        loss_mode = self.sel["mode"] == "loss"
        self.fields["loss"].disabled = not loss_mode
        self.fields["stop"].disabled = loss_mode

    # ---------- 计算 ----------
    def num(self, key, name):
        try:
            v = float(self.fields[key].text.strip())
        except ValueError:
            raise ValueError(f"{name} 不是有效数字")
        if not math.isfinite(v):
            raise ValueError(f"{name} 必须是有限数值")
        if v <= 0:
            raise ValueError(f"{name} 必须大于0")
        return v

    def on_calc(self, *_):
        f = self.fields
        try:
            B = self.num("buy", "买入价")
            L = self.num("lev", "杠杆倍数")
            if L < 1:
                raise ValueError("杠杆倍数至少为1")
            T = self.num("total", "总资金")
            cost = self.num("cost", "投入成本") if f["cost"].text.strip() else None
            m = self.sel["mode"]
            loss_value, stop_price = 0.0, 0.0
            if m == "loss":
                loss_value = self.num("loss", "亏损上限数值")
            else:
                stop_price = self.num("stop", "止损价")
            target = self.num("target", "目标总资金") if f["target"].text.strip() else None
            out = calculate(self.sel["dir"], B, L, T, m, loss_value,
                            self.sel["kind"] == "amt", stop_price, target, invested_cost=cost)
        except ValueError as ex:
            out = {"ok": False, "lines": [], "warnings": [str(ex)]}
        self.show(out)
        Window.release_all_keyboards()

    def show(self, out):
        if not out["ok"]:
            self.result.text = "\n".join(f"错误：{w}" for w in out["warnings"])
        else:
            self.result.text = "\n".join(out["lines"] + [f"警告：{w}" for w in out["warnings"]])


if __name__ == "__main__":
    StopLossApp().run()
