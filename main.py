# main.py
import tkinter as tk
from tkinter import ttk, messagebox

from db import init_db, save_rate, get_saved_rate
from api import fetch_rates


class CurrencyConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Конвертер валют и калькулятор кредита")
        self.geometry("520x620")
        self.resizable(False, False)

        # переменные для кредита
        self.loan_var = tk.DoubleVar(value=100000.0)      # сумма кредита
        self.loan_time_var = tk.IntVar(value=12)          # срок в месяцах
        self.annual_interest_var = tk.DoubleVar(value=17.0)  # годовая ставка

        # переменные для валют
        self.base_var = tk.StringVar(value="RUB")
        self.target_var = tk.StringVar(value="USD")

        # сюда запоминаем последний рассчитанный платёж
        self.last_monthly_payment = 0.0

        # создаём интерфейс
        self.create_widgets()

        # инициализируем БД
        init_db()
        self.log("База данных инициализирована")

    # ---------- UI ----------

    def create_widgets(self) -> None:
        padding = {"padx": 10, "pady": 5}

        # Сумма кредита
        ttk.Label(self, text="Сумма кредита:").grid(
            row=0, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.loan_var).grid(
            row=0, column=1, sticky="ew", **padding
        )
        ttk.Label(self, text="RUB").grid(row=0, column=2, sticky="w", **padding)

        # Срок кредита
        ttk.Label(self, text="Срок кредита:").grid(
            row=1, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.loan_time_var).grid(
            row=1, column=1, sticky="ew", **padding
        )
        ttk.Label(self, text="мес.").grid(row=1, column=2, sticky="w", **padding)

        # Процентная ставка
        ttk.Label(self, text="Процентная ставка:").grid(
            row=2, column=0, sticky="w", **padding
        )
        ttk.Entry(self, textvariable=self.annual_interest_var).grid(
            row=2, column=1, sticky="ew", **padding
        )
        ttk.Label(self, text="%").grid(row=2, column=2, sticky="w", **padding)

        # Кнопка "Рассчитать"
        ttk.Button(self, text="Рассчитать", command=self.calculate_loan).grid(
            row=3, column=0, columnspan=3, pady=(10, 10)
        )

        # Результаты кредита
        self.monthly_label = ttk.Label(self, text="Ежемесячный платёж: 0 RUB")
        self.monthly_label.grid(
            row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0)
        )

        self.loan_sum_label = ttk.Label(self, text="Сумма всех платежей: 0 RUB")
        self.loan_sum_label.grid(
            row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0)
        )

        self.interest_label = ttk.Label(self, text="Начисленные проценты: 0 RUB")
        self.interest_label.grid(
            row=6, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 10)
        )

        # Разделитель
        ttk.Separator(self, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky="ew", pady=10
        )

        # Базовая валюта
        ttk.Label(self, text="Базовая валюта:").grid(
            row=8, column=0, sticky="w", **padding
        )
        ttk.Label(self, textvariable=self.base_var).grid(
            row=8, column=1, sticky="w", **padding
        )

        # Целевая валюта
        ttk.Label(self, text="Целевая валюта:").grid(
            row=9, column=0, sticky="w", **padding
        )
        self.target_entry = ttk.Combobox(
            self,
            textvariable=self.target_var,
            state="readonly",
            values=["USD", "EUR", "GBP"],  # при первом запуске, потом обновим из БД
        )
        self.target_entry.grid(row=9, column=1, sticky="ew", **padding)

        # Кнопка "Конвертировать"
        ttk.Button(self, text="Конвертировать", command=self.convert).grid(
            row=10, column=0, columnspan=3, pady=(10, 5)
        )

        # Результат конвертации
        self.result_label = ttk.Label(self, text="Результат: 0.00")
        self.result_label.grid(
            row=11, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 10)
        )

        # Кнопка "Обновить курсы"
        ttk.Button(self, text="Обновить курсы", command=self.update_db).grid(
            row=12, column=0, columnspan=3, pady=(5, 10)
        )

        # Логгер
        ttk.Label(self, text="Лог:").grid(
            row=13, column=0, columnspan=3, sticky="w", padx=10
        )
        self.log_text = tk.Text(self, height=8, state="disabled")
        self.log_text.grid(
            row=14, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10)
        )

        # чтобы поле логов тянулось по ширине
        self.columnconfigure(1, weight=1)

    # ---------- Вспомогательные методы ----------

    def log(self, message: str) -> None:
        """Вывод сообщения в лог-панель."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def is_loan_invalid(self, value: float, message: str) -> bool:
        """Проверка, что значение > 0."""
        if value <= 0:
            messagebox.showerror("Ошибка", message)
            self.log(message)
            return True
        return False

    # ---------- Логика кредита ----------

    def calculate_loan(self) -> None:
        """Рассчёт ежемесячного платежа, общей суммы и процентов."""
        try:
            loan = float(self.loan_var.get())
            months = int(self.loan_time_var.get())
            annual_interest = float(self.annual_interest_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Ошибка", "Введите корректные значения кредита.")
            return

        if self.is_loan_invalid(loan, "Сумма кредита должна быть больше 0"):
            return
        if self.is_loan_invalid(months, "Срок кредита должен быть больше 0"):
            return
        if self.is_loan_invalid(
            annual_interest, "Процентная ставка должна быть больше 0"
        ):
            return

        # месячная ставка
        monthly_interest = annual_interest / 12 / 100

        # аннуитетная формула
        if monthly_interest == 0:
            monthly_payment = loan / months
        else:
            factor = (monthly_interest * (1 + monthly_interest) ** months) / (
                (1 + monthly_interest) ** months - 1
            )
            monthly_payment = loan * factor

        total_payment = monthly_payment * months
        total_interest = total_payment - loan

        monthly_payment = round(monthly_payment, 2)
        total_payment = round(total_payment, 2)
        total_interest = round(total_interest, 2)

        self.last_monthly_payment = monthly_payment

        self.monthly_label.config(
            text=f"Ежемесячный платёж: {monthly_payment} RUB"
        )
        self.loan_sum_label.config(
            text=f"Сумма всех платежей: {total_payment} RUB"
        )
        self.interest_label.config(
            text=f"Начисленные проценты: {total_interest} RUB"
        )

        self.log(
            f"Рассчитан кредит: платёж {monthly_payment} RUB, всего {total_payment} RUB, проценты {total_interest} RUB"
        )

    # ---------- Конвертация валют ----------

    def convert(self) -> None:
        """Конвертация ежемесячного платежа из RUB в выбранную валюту."""
        if self.last_monthly_payment <= 0:
            messagebox.showinfo("Информация", "Сначала рассчитайте кредит.")
            return

        target = self.target_var.get()
        if not target:
            messagebox.showerror("Ошибка", "Выберите целевую валюту.")
            return

        if target == self.base_var.get():
            amount = self.last_monthly_payment
            self.result_label.config(text=f"Результат: {amount:.2f} {target}")
            return

        try:
            if target == "RUB":
                rate = 1.0
            else:
                rate = get_saved_rate(target)
            if not rate:
                raise ValueError("Курс не найден")
        except Exception as exc:
            messagebox.showerror(
                "Ошибка", f"Не удалось получить курс для {target}: {exc}"
            )
            self.log(f"Ошибка получения курса для {target}: {exc}")
            return

        # В API ЦБ курс = сколько RUB за 1 единицу валюты
        amount_target = self.last_monthly_payment / rate

        self.result_label.config(
            text=f"Результат: {amount_target:.2f} {target}"
        )
        self.log(
            f"Конвертация {self.last_monthly_payment} RUB -> {amount_target:.2f} {target}"
        )

    # ---------- Обновление БД ----------

    def update_db(self) -> None:
        """Получить актуальные курсы через API и сохранить их в БД."""
        self.log("Обновление курсов валют...")
        try:
            data = fetch_rates()
            valute = data.get("Valute", {})

            # базовая валюта
            save_rate(0, "RUB", 1.0)

            # сохраняем все валюты из ответа ЦБ
            for idx, (code, info) in enumerate(valute.items(), start=1):
                value = float(info["Value"])
                nominal = float(info.get("Nominal", 1))
                rate = value / nominal  # RUB за 1 единицу валюты
                save_rate(idx, code, rate)

            # обновляем список валют в комбобоксе
            codes = sorted(["RUB"] + list(valute.keys()))
            self.target_entry["values"] = codes
            if self.target_var.get() not in codes:
                self.target_var.set("USD" if "USD" in codes else codes[0])

            self.log("Курсы валют обновлены.")
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось обновить курсы: {exc}")
            self.log(f"Ошибка обновления курсов: {exc}")


if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()
