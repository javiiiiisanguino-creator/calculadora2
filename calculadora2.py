"""
Calculadora en Kivy con historial de las ultimas 5 operaciones.

Equivalente en Kivy de calculadora.py (version tkinter).
"""

import math
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty, ListProperty, NumericProperty, StringProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

os.environ.setdefault("KIVY_NO_ARGS", "1")

BLUE_DARK = "#1a237e"
BLUE_MED = "#283593"
BLUE_LIGHT = "#3949ab"
BLUE_ACCENT = "#5c6bc0"
BLUE_PALE = "#e8eaf6"
WHITE = "#ffffff"
GRAY_LIGHT = "#f5f5f5"
GRAY_BORDER = "#d0d3d8"
GRAY_MUTED = "#9e9e9e"
RED = "#c62828"
RED_HOVER = "#e53935"

MAX_HISTORIAL = 5
SIMBOLOS = {"+": "+", "-": "-", "*": "×", "/": "÷"}

BOTONES = [
    ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("/", 0, 3),
    ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("*", 1, 3),
    ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), ("-", 2, 3),
    ("0", 3, 0), (".", 3, 1), ("C", 3, 2), ("+", 3, 3),
]


def formatear(valor):
    if valor == int(valor) and abs(valor) < 1e16:
        return str(int(valor))
    return f"{valor:.10g}"


class Boton(Label):
    """Boton redondeado con estados presionado/normal."""

    __events__ = ("on_press",)

    bg_color = ListProperty([0, 0, 0, 1])
    bg_hover = ListProperty([0, 0, 0, 1])

    _presionado = BooleanProperty(False)
    _sobre = BooleanProperty(False)

    def __init__(self, texto, bg, bg_hover, fg, tamano=16, **kwargs):
        super().__init__(
            text=texto,
            color=fg,
            font_name="Roboto",
            font_size=sp(tamano),
            bold=True,
            **kwargs
        )
        self.bg_color = bg
        self.bg_hover = bg_hover

    def _color_actual(self):
        return self.bg_hover if (self._presionado or self._sobre) else self.bg_color

    def _refrescar(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._color_actual())
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)],
            )

    def on_pos(self, *args):
        self._refrescar()

    def on_size(self, *args):
        self._refrescar()

    def on__presionado(self, *args):
        self._refrescar()

    def on__sobre(self, *args):
        self._refrescar()

    def on_mouse_motion(self, window, pos):
        """Hover real: se sigue al raton aunque no haya pulsacion."""
        # pos viene en coordenadas de ventana; hay que TranslatedRelative -> local
        relative = self.to_local(*self.to_widget(*pos))
        self._sobre = self.collide_point(*relative)
        return False

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._presionado = True
        self._sobre = True
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        self._sobre = self.collide_point(*touch.pos)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        dentro = self.collide_point(*touch.pos)
        self._presionado = False
        # el raton puede haberse ido de la ventana: hay que soltar el hover
        self._sobre = dentro
        if dentro:
            self.dispatch("on_press")
        return True

    def on_press(self):
        pass


class BotonCalculadora(Boton):
    def __init__(self, texto, bg, bg_hover, fg, calculadora, accion, **kwargs):
        super().__init__(texto, bg, bg_hover, fg, **kwargs)
        self.calculadora = calculadora
        self.accion = accion

    def on_press(self):
        self.accion(self.text)


class PanelHistorial(BoxLayout):
    """Tarjeta con las ultimas operaciones, de la mas reciente a la mas antigua."""

    historial = ListProperty([])

    def __init__(self, calculadora, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.calculadora = calculadora
        self.spacing = dp(2)
        self.padding = (dp(10), dp(8), dp(10), dp(8))

        titulo = Label(
            text=f"Historial (ultimas {MAX_HISTORIAL} operaciones)",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=BLUE_MED,
            font_name="Roboto",
            font_size=sp(12),
            bold=True,
        )
        titulo.bind(size=titulo.setter("text_size"))
        self.add_widget(titulo)

        self.contenedor = BoxLayout(orientation="vertical", spacing=dp(2))
        self.add_widget(self.contenedor)

        btn = Boton(
            "Limpiar historial",
            self._rgba(BLUE_PALE),
            self._rgba(BLUE_ACCENT),
            BLUE_DARK,
            tamano=11,
        )
        btn.bind(on_press=lambda *_: self.calculadora.limpiar_historial())
        fila_boton = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            padding=(0, dp(4), 0, 0),
        )
        fila_boton.add_widget(Widget())
        fila_boton.add_widget(btn)
        self.add_widget(fila_boton)

        self._refrescar()

    @staticmethod
    def _rgba(hex_color):
        return [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1]

    def on_historial(self, *args):
        self._refrescar()

    def _refrescar(self):
        self.contenedor.clear_widgets()

        if not self.historial:
            vacio = Label(
                text="Sin operaciones",
                size_hint_y=None,
                height=dp(24),
                halign="left",
                valign="middle",
                color=GRAY_MUTED,
                font_name="Roboto",
                font_size=sp(11),
                italic=True,
            )
            vacio.bind(size=vacio.setter("text_size"))
            self.contenedor.add_widget(vacio)
            return

        for indice, (a, b, op, resultado) in enumerate(self.historial, start=1):
            fila = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))

            num = Label(
                text=f"{indice}.",
                size_hint_x=None,
                width=dp(24),
                color=GRAY_MUTED,
                font_size=sp(11),
                halign="left",
                valign="middle",
            )
            num.bind(size=num.setter("text_size"))
            fila.add_widget(num)

            izq = Label(
                text=f"{formatear(a)} {SIMBOLOS[op]} {formatear(b)}",
                color=BLUE_MED,
                font_name="RobotoMono-Regular",
                font_size=sp(12),
                halign="left",
                valign="middle",
            )
            izq.bind(size=izq.setter("text_size"))
            fila.add_widget(izq)

            der = Label(
                text=f"= {formatear(resultado)}",
                size_hint_x=None,
                width=dp(110),
                color=BLUE_DARK,
                font_name="RobotoMono-Regular",
                font_size=sp(12),
                bold=True,
                halign="right",
                valign="middle",
            )
            der.bind(size=der.setter("text_size"))
            fila.add_widget(der)

            self.contenedor.add_widget(fila)


class Calculadora(BoxLayout):
    """Layout raiz: cabecera, pantalla, teclado, historial y pie."""

    pantalla_texto = StringProperty("0")
    operacion_texto = StringProperty("")
    error_activo = BooleanProperty(False)
    historial = ListProperty([])

    _operacion = None
    _operandos = []
    _nuevo_numero = False

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(20), dp(16), dp(20), dp(16)),
            spacing=dp(12),
            **kwargs
        )
        self._construir_interfaz()

    # ------------------------------------------------------------------ UI

    def _construir_interfaz(self):
        header = Label(
            text="Calculadora Basica",
            size_hint_y=None,
            height=dp(52),
            color=WHITE,
            font_name="Roboto",
            font_size=sp(18),
            bold=True,
        )
        self.add_widget(header)
        self._pintar_fondo(header, BLUE_DARK, dp(8))

        pantalla = Label(
            text=self.pantalla_texto,
            size_hint_y=None,
            height=dp(64),
            color=BLUE_DARK,
            font_name="RobotoMono-Regular",
            font_size=sp(22),
            bold=True,
            halign="right",
            valign="middle",
        )
        pantalla.bind(size=pantalla.setter("text_size"))
        pantalla.bind(text_size=lambda w, v: self._pintar_pantalla(w))
        pantalla.bind(pos=lambda w, v: self._pintar_pantalla(w))
        pantalla.bind(size=lambda w, v: self._pintar_pantalla(w))
        # el estado es la fuente de verdad: la etiqueta refleja pantalla_texto
        self.bind(
            pantalla_texto=lambda _self, valor: setattr(pantalla, "text", valor)
        )
        self.pantalla = pantalla
        self.add_widget(pantalla)
        self._pintar_pantalla(pantalla)

        self.etiqueta_operacion = Label(
            text=self.operacion_texto,
            size_hint_y=None,
            height=dp(20),
            color=BLUE_DARK,
            font_name="Roboto",
            font_size=sp(12),
            halign="right",
            valign="middle",
        )
        self.etiqueta_operacion.bind(
            size=self.etiqueta_operacion.setter("text_size"))
        self.bind(
            operacion_texto=lambda _self, valor: setattr(
                self.etiqueta_operacion, "text", valor)
        )
        self.add_widget(self.etiqueta_operacion)

        self._construir_teclado()
        self._construir_historial()

        footer = Label(
            text="Realizado por Javier Sanguino - 2026",
            size_hint_y=None,
            height=dp(26),
            color=BLUE_DARK,
            font_name="Roboto",
            font_size=sp(10),
        )
        self.add_widget(footer)
        self._pintar_fondo(footer, BLUE_PALE, dp(6))

    def _pintar_fondo(self, widget, color, radio):
        """Dibuja el fondo redondeado y lo mantiene al cambiar el tamano."""

        def refrescar(*_args):
            widget.canvas.before.clear()
            with widget.canvas.before:
                Color(*self._rgba(color))
                RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radio])

        # el layout aun no esta calculado al construir: hay que redibujar luego
        widget.bind(pos=refrescar, size=refrescar)
        refrescar()

    def _pintar_pantalla(self, widget):
        widget.canvas.before.clear()
        with widget.canvas.before:
            Color(*self._rgba(WHITE))
            RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(8)])
            Color(*self._rgba(RED if self.error_activo else BLUE_ACCENT))
            r = dp(1.5)
            RoundedRectangle(
                pos=(widget.x + r, widget.y + r),
                size=(widget.width - 2 * r, widget.height - 2 * r),
                radius=[dp(8)],
                line_width=r * 2,
            )

    @staticmethod
    def _rgba(hex_color):
        return [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1]

    def _construir_teclado(self):
        grid = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(260))
        self.add_widget(grid)

        for texto, fila, col in BOTONES:
            if texto in SIMBOLOS:
                bg, bg_hover, fg = BLUE_MED, BLUE_DARK, WHITE
                accion = self.presionar_operador
            elif texto == "C":
                bg, bg_hover, fg = RED, RED_HOVER, WHITE
                accion = self.presionar_limpiar
            else:
                # hover sutil: los numeros nunca deben parecer un operador
                bg, bg_hover, fg = BLUE_PALE, "#d5d9f0", BLUE_DARK
                accion = self.presionar_digito

            boton = BotonCalculadora(
                texto,
                self._rgba(bg),
                self._rgba(bg_hover),
                fg,
                self,
                accion,
            )
            grid.add_widget(boton)

        btn_igual = BotonCalculadora(
            "=", self._rgba(BLUE_ACCENT), self._rgba(BLUE_LIGHT), WHITE,
            self, self.presionar_igual, tamano=18,
        )
        grid.add_widget(btn_igual)

    def _construir_historial(self):
        self.tarjeta_historial = PanelHistorial(self)
        self.tarjeta_historial.size_hint_y = None
        self.tarjeta_historial.height = dp(24 + MAX_HISTORIAL * 22 + 28 + 24)
        self.bind(historial=self._sync_historial)
        self.tarjeta_historial.bind(size=lambda w, v: self._pintar_fondo(w, WHITE, dp(6)))
        self.add_widget(self.tarjeta_historial)
        self._pintar_fondo(self.tarjeta_historial, WHITE, dp(6))

    # ----------------------------------------------------------- historial

    def _sync_historial(self, *_args):
        self.tarjeta_historial.historial = self.historial

    def registrar_historial(self, a, b, op, resultado):
        historial = [(a, b, op, resultado)] + list(self.historial)
        self.historial = historial[:MAX_HISTORIAL]

    def limpiar_historial(self):
        self.historial = []

    # ------------------------------------------------------------- logica

    def digito(self, texto):
        if self.error_activo:
            self.reiniciar()

        actual = self.pantalla_texto
        if self._nuevo_numero:
            actual = "0"
            self._nuevo_numero = False

        if texto == ".":
            if "." in actual:
                return
            if actual in ("0", "-0"):
                self.cambiar_texto("0.")
            else:
                self.cambiar_texto(actual + ".")
            return

        if actual in ("0", "-0"):
            self.cambiar_texto(texto)
        else:
            self.cambiar_texto(actual + texto)

    def operador(self, op):
        if self.error_activo:
            self.reiniciar()

        valor = self.leer_pantalla()
        if valor is None:
            return

        if self._operacion is not None and not self._nuevo_numero:
            resultado = self.calcular(self._operandos[0], valor, self._operacion)
            if resultado is None:
                return
            self.registrar_historial(
                self._operandos[0], valor, self._operacion, resultado
            )
            self._operandos = [resultado]
            self.cambiar_texto(formatear(resultado))
        else:
            self._operandos = [valor]

        self._operacion = op
        self._nuevo_numero = True
        self.operacion_texto = f"{formatear(self._operandos[0])} {SIMBOLOS[op]}"

    def igual(self):
        if self._operacion is None or len(self._operandos) < 1:
            return

        valor = self.leer_pantalla()
        if valor is None:
            return

        a, b, op = self._operandos[0], valor, self._operacion
        resultado = self.calcular(a, b, op)

        self._operacion = None
        self._operandos = []
        self._nuevo_numero = True
        self.operacion_texto = ""

        if resultado is None:
            return

        self.registrar_historial(a, b, op, resultado)
        self.cambiar_texto(formatear(resultado))

    def calcular(self, a, b, op):
        try:
            if op == "+":
                resultado = a + b
            elif op == "-":
                resultado = a - b
            elif op == "*":
                resultado = a * b
            elif op == "/":
                if b == 0:
                    self.error("No se puede dividir entre cero")
                    return None
                resultado = a / b
            else:
                self.error("Operacion no valida")
                return None

            if not math.isfinite(resultado):
                self.error("El resultado es demasiado grande")
                return None
            return resultado
        except ZeroDivisionError:
            self.error("No se puede dividir entre cero")
            return None
        except (OverflowError, ValueError):
            self.error("Error en la operacion")
            return None

    def leer_pantalla(self):
        try:
            valor = float(self.pantalla_texto)
            if not math.isfinite(valor):
                raise ValueError
            return valor
        except ValueError:
            self.error("Entrada no valida")
            return None

    def cambiar_texto(self, texto):
        self.pantalla_texto = texto
        self.error_activo = False

    def error(self, mensaje):
        self.pantalla_texto = mensaje
        self.error_activo = True
        self._operacion = None
        self._operandos = []
        self._nuevo_numero = True
        self.operacion_texto = ""
        self.mostrar_error(mensaje)

    def mostrar_error(self, mensaje):
        contenido = Label(
            text=mensaje,
            color=RED,
            font_name="Roboto",
            font_size=sp(13),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(50),
        )
        contenido.bind(size=contenido.setter("text_size"))
        popup = Popup(
            title="Error",
            content=contenido,
            size_hint=(None, None),
            size=(dp(320), dp(190)),
            auto_dismiss=True,
        )
        popup.open()

    def reiniciar(self):
        self._operacion = None
        self._operandos = []
        self._nuevo_numero = False
        self.error_activo = False
        self.operacion_texto = ""
        self.cambiar_texto("0")

    # ------------------------------------------------------- pulsaciones UI

    def presionar_digito(self, texto):
        self.digito(texto)

    def presionar_operador(self, op):
        self.operador(op)

    def presionar_igual(self, _texto=None):
        self.igual()

    def presionar_limpiar(self, _texto=None):
        self.reiniciar()

    # ----------------------------------------------------------- teclado

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if codepoint and (codepoint.isdigit() or codepoint == "."):
            self.digito(codepoint)
            return True
        if codepoint in SIMBOLOS:
            self.operador(codepoint)
            return True
        if codepoint in ("=", "\r", "\n"):
            self.igual()
            return True
        if key == 8:  # backspace
            if self.error_activo:
                self.reiniciar()
                return True
            if self._nuevo_numero:
                self.cambiar_texto("0")
                return True

            actual = self.pantalla_texto
            nuevo = actual[:-1] if len(actual) > 1 else "0"
            if nuevo in ("", "-", "+", "-."):
                nuevo = "0"
            self.cambiar_texto(nuevo)
            return True
        if key == 27:  # escape
            self.reiniciar()
            return True
        return False


class CalculadoraApp(App):
    title = "Calculadora"

    def build(self):
        Window.clearcolor = self._rgba(GRAY_LIGHT)
        Window.size = (dp(380), dp(700))
        return Calculadora()

    @staticmethod
    def _rgba(hex_color):
        return [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1]


def main():
    CalculadoraApp().run()


if __name__ == "__main__":
    main()
