import tkinter as tk
from datetime import datetime
from collections import defaultdict
from io import BytesIO

import requests
from PIL import Image, ImageTk

from weather_service import (
    get_current_weather,
    get_forecast,
    WeatherAPIError
)


class WeatherApp:
    BG = "#F1F5F9"
    NAVY = "#172B4D"
    MUTED = "#64748B"
    BLUE = "#2563EB"
    CARD = "#FFFFFF"
    SOFT = "#F1F5F9"

    def __init__(self, root):
        self.root = root
        self.root.title("Weather Studio")
        self.root.geometry("900x930")
        self.root.minsize(760, 780)
        self.root.configure(bg=self.BG)

        self.unit = "C"
        self.current_weather = None
        self.forecast_data = []
        self.icon_cache = {}

        self.create_widgets()

    def create_widgets(self):
        # Keep the title and search controls fixed while the weather dashboard scrolls.
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=30, pady=(18, 10))

        tk.Label(
            header, text="Weather Studio",
            font=("Arial", 25, "bold"),
            bg=self.BG, fg=self.NAVY
        ).pack(anchor="w")

        tk.Label(
            header, text="Real-time weather and forecast information",
            font=("Arial", 10), bg=self.BG, fg=self.MUTED
        ).pack(anchor="w", pady=(3, 0))

        search_frame = tk.Frame(
            self.root, bg=self.CARD, padx=15, pady=13,
            highlightbackground="#DCE4EE", highlightthickness=1
        )
        search_frame.pack(fill="x", padx=30, pady=5)

        self.city_var = tk.StringVar()
        self.city_entry = tk.Entry(
            search_frame, textvariable=self.city_var,
            font=("Arial", 12), relief="solid", bd=1,
            fg=self.NAVY
        )
        self.city_entry.pack(
            side="left", fill="x", expand=True,
            ipady=9, padx=(0, 10)
        )
        self.city_entry.insert(0, "Enter city name")
        self.city_entry.config(fg="#94A3B8")
        self.city_entry.bind("<FocusIn>", self.clear_placeholder)
        self.city_entry.bind("<FocusOut>", self.restore_placeholder)
        self.city_entry.bind("<Return>", lambda event: self.get_weather())

        self.search_button = tk.Button(
            search_frame, text="Get Weather", command=self.get_weather,
            font=("Arial", 10, "bold"), bg=self.BLUE, fg="white",
            activebackground="#1D4ED8", activeforeground="white",
            relief="flat", cursor="hand2", padx=18, pady=10
        )
        self.search_button.pack(side="right")

        # Scrollable dashboard area.
        dashboard_shell = tk.Frame(self.root, bg=self.BG)
        dashboard_shell.pack(fill="both", expand=True, padx=(18, 8), pady=(4, 10))

        self.dashboard_canvas = tk.Canvas(
            dashboard_shell, bg=self.BG, highlightthickness=0,
            borderwidth=0
        )
        scrollbar = tk.Scrollbar(
            dashboard_shell, orient="vertical",
            command=self.dashboard_canvas.yview
        )
        self.dashboard_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.dashboard_canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = tk.Frame(self.dashboard_canvas, bg=self.BG)
        self.content_window = self.dashboard_canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )

        self.content_frame.bind(
            "<Configure>",
            lambda event: self.dashboard_canvas.configure(
                scrollregion=self.dashboard_canvas.bbox("all")
            )
        )
        self.dashboard_canvas.bind(
            "<Configure>",
            lambda event: self.dashboard_canvas.itemconfigure(
                self.content_window, width=event.width
            )
        )

        # Enable mouse-wheel scrolling when the pointer is over the dashboard.
        self.dashboard_canvas.bind("<Enter>", self._bind_mousewheel)
        self.dashboard_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.status_label = tk.Label(
            self.content_frame, text="Enter a city to view its weather.",
            font=("Arial", 9), bg=self.BG, fg=self.MUTED, anchor="w"
        )
        self.status_label.pack(fill="x", padx=17, pady=(5, 3))

        self.current_frame = self.make_card(self.content_frame, padx=22, pady=16)
        self.current_frame.pack(fill="x", padx=12, pady=7)

        top_row = tk.Frame(self.current_frame, bg=self.CARD)
        top_row.pack(fill="x")

        self.location_label = tk.Label(
            top_row, text="Location", font=("Arial", 17, "bold"),
            bg=self.CARD, fg=self.NAVY
        )
        self.location_label.pack(side="left")

        self.unit_button = tk.Button(
            top_row, text="Show °F", command=self.toggle_unit,
            font=("Arial", 9, "bold"), bg="#E8EEF8", fg="#1E40AF",
            relief="flat", cursor="hand2", padx=12, pady=6,
            state="disabled"
        )
        self.unit_button.pack(side="right")

        weather_main = tk.Frame(self.current_frame, bg=self.CARD)
        weather_main.pack(fill="x", pady=(5, 10))

        # Do not constrain this label with text-based width/height values:
        # those values clipped the 116x116 current-weather image.
        self.icon_label = tk.Label(
            weather_main, text="Weather", font=("Arial", 9),
            bg=self.CARD, fg=self.MUTED, anchor="center"
        )
        self.icon_label.pack(side="left", padx=(0, 12))

        temperature_frame = tk.Frame(weather_main, bg=self.CARD)
        temperature_frame.pack(side="left", padx=5)

        self.temperature_label = tk.Label(
            temperature_frame, text="--°",
            font=("Arial", 36, "bold"), bg=self.CARD, fg=self.NAVY
        )
        self.temperature_label.pack(anchor="w")

        self.condition_label = tk.Label(
            temperature_frame, text="Weather condition",
            font=("Arial", 11), bg=self.CARD, fg=self.MUTED
        )
        self.condition_label.pack(anchor="w")

        details = tk.Frame(self.current_frame, bg=self.CARD)
        details.pack(fill="x", pady=(5, 0))
        self.humidity_value = self.create_detail(details, "Humidity", "--")
        self.wind_value = self.create_detail(details, "Wind Speed", "--")
        self.feels_value = self.create_detail(details, "Feels Like", "--")

        self.hourly_frame = self.make_card(self.content_frame, padx=18, pady=13)
        self.hourly_frame.pack(fill="x", padx=12, pady=7)

        tk.Label(
            self.hourly_frame, text="Next 6 Forecast Periods",
            font=("Arial", 13, "bold"), bg=self.CARD, fg=self.NAVY
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            self.hourly_frame,
            text="Forecast data is provided in 3-hour intervals.",
            font=("Arial", 8), bg=self.CARD, fg=self.MUTED
        ).pack(anchor="w", pady=(0, 8))

        self.hourly_container = tk.Frame(self.hourly_frame, bg=self.CARD)
        self.hourly_container.pack(fill="x")

        self.daily_frame = self.make_card(self.content_frame, padx=18, pady=13)
        self.daily_frame.pack(fill="x", padx=12, pady=(7, 14))

        tk.Label(
            self.daily_frame, text="5-Day Forecast",
            font=("Arial", 13, "bold"), bg=self.CARD, fg=self.NAVY
        ).pack(anchor="w", pady=(0, 9))

        tk.Label(
            self.daily_frame,
            text="Daily temperature range is estimated from available 3-hour forecasts.",
            font=("Arial", 8), bg=self.CARD, fg=self.MUTED
        ).pack(anchor="w", pady=(0, 8))

        self.daily_container = tk.Frame(self.daily_frame, bg=self.CARD)
        self.daily_container.pack(fill="x")

    def _bind_mousewheel(self, event=None):
        self.dashboard_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        self.dashboard_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        # Windows reports wheel movement in multiples of 120.
        self.dashboard_canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units"
        )

    def make_card(self, parent, padx=16, pady=12):
        return tk.Frame(
            parent, bg=self.CARD, padx=padx, pady=pady,
            highlightbackground="#DCE4EE", highlightthickness=1
        )

    def create_detail(self, parent, title, initial_value):
        frame = tk.Frame(parent, bg=self.SOFT, padx=13, pady=10)
        frame.pack(side="left", fill="x", expand=True, padx=4)

        tk.Label(
            frame, text=title, font=("Arial", 9),
            bg=self.SOFT, fg=self.MUTED
        ).pack(anchor="w")

        value = tk.Label(
            frame, text=initial_value, font=("Arial", 12, "bold"),
            bg=self.SOFT, fg=self.NAVY
        )
        value.pack(anchor="w", pady=(3, 0))
        return value

    def clear_placeholder(self, event):
        if self.city_var.get() == "Enter city name":
            self.city_var.set("")
            self.city_entry.config(fg=self.NAVY)

    def restore_placeholder(self, event):
        if not self.city_var.get().strip():
            self.city_var.set("Enter city name")
            self.city_entry.config(fg="#94A3B8")

    def show_status(self, message, error=False):
        self.status_label.config(
            text=message,
            fg="#DC2626" if error else self.MUTED
        )

    def get_weather(self):
        city = self.city_var.get().strip()
        if not city or city == "Enter city name":
            self.show_status("Please enter a city name.", error=True)
            return

        self.search_button.config(state="disabled")
        self.show_status("Fetching weather information...")
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        try:
            current = get_current_weather(city)
            forecast = get_forecast(city)

            if not forecast:
                raise WeatherAPIError("No forecast information is available.")

            self.current_weather = current
            self.forecast_data = forecast

            self.display_current_weather()
            self.display_hourly_forecast()
            self.display_daily_forecast()
            self.show_status(
                f"Weather updated for {current['city']}, {current['country']}."
            )

        except WeatherAPIError as error:
            self.show_status(str(error), error=True)
        except (KeyError, ValueError, TypeError) as error:
            self.show_status(
                f"Unexpected weather data received: {error}", error=True
            )
        finally:
            self.search_button.config(state="normal")
            self.root.config(cursor="")

    def temperature_text(self, temperature_c):
        if self.unit == "C":
            return f"{temperature_c:.1f}°C"
        return f"{(temperature_c * 9 / 5) + 32:.1f}°F"

    def display_current_weather(self):
        data = self.current_weather
        self.location_label.config(
            text=f"{data['city']}, {data['country']}"
        )
        self.temperature_label.config(
            text=self.temperature_text(data["temperature_c"])
        )
        self.condition_label.config(text=data["description"])
        self.humidity_value.config(text=f"{data['humidity']}%")
        self.wind_value.config(text=f"{data['wind_speed']:.1f} m/s")

        feels_key = "feels_like_c" if self.unit == "C" else "feels_like_f"
        self.feels_value.config(
            text=f"{data[feels_key]:.1f}°{'C' if self.unit == 'C' else 'F'}"
        )

        self.unit_button.config(
            state="normal",
            text="Show °F" if self.unit == "C" else "Show °C"
        )
        self.set_weather_icon(self.icon_label, data["icon"], size=(116, 116))

    def toggle_unit(self):
        if self.current_weather is None:
            return
        self.unit = "F" if self.unit == "C" else "C"
        self.display_current_weather()
        self.display_hourly_forecast()
        self.display_daily_forecast()

    def load_icon(self, icon_code, size):
        cache_key = (icon_code, size)
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        response = requests.get(url, timeout=6)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGBA")
        image = image.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.icon_cache[cache_key] = photo
        return photo

    def set_weather_icon(self, label, icon_code, size=(64, 64)):
        try:
            photo = self.load_icon(icon_code, size)
            label.config(image=photo, text="")
            label.image = photo  # Keep a reference so Tkinter does not discard it.
        except (
            requests.exceptions.RequestException,
            OSError,
            ValueError,
            tk.TclError
        ):
            label.config(image="", text="Weather", fg=self.MUTED)
            label.image = None

    def display_hourly_forecast(self):
        for widget in self.hourly_container.winfo_children():
            widget.destroy()

        for item in self.forecast_data[:6]:
            period = tk.Frame(
                self.hourly_container, bg=self.SOFT, padx=5, pady=8
            )
            period.pack(
                side="left", fill="both", expand=True, padx=3
            )

            dt = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")
            tk.Label(
                period, text=dt.strftime("%a %H:%M"),
                font=("Arial", 9, "bold"), bg=self.SOFT, fg=self.NAVY
            ).pack()

            icon_label = tk.Label(period, bg=self.SOFT)
            icon_label.pack(pady=2)
            self.set_weather_icon(icon_label, item["icon"], size=(64, 64))

            tk.Label(
                period, text=self.temperature_text(item["temperature_c"]),
                font=("Arial", 10, "bold"), bg=self.SOFT, fg=self.NAVY
            ).pack()

            tk.Label(
                period, text=item["description"],
                font=("Arial", 8), bg=self.SOFT, fg=self.MUTED,
                wraplength=105, justify="center"
            ).pack(pady=(3, 0))

    def display_daily_forecast(self):
        for widget in self.daily_container.winfo_children():
            widget.destroy()

        grouped = defaultdict(list)
        for item in self.forecast_data:
            dt = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")
            grouped[dt.date()].append(item)

        dates = sorted(grouped)[:5]

        for date_value in dates:
            items = grouped[date_value]
            temps = [item["temperature_c"] for item in items]

            representative = min(
                items,
                key=lambda item: abs(
                    datetime.strptime(
                        item["datetime"], "%Y-%m-%d %H:%M:%S"
                    ).hour - 12
                )
            )
        

            row = tk.Frame(
                self.daily_container, bg="#F8FAFC", padx=12, pady=8
            )
            row.pack(fill="x", pady=4)

            tk.Label(
                row, text=date_value.strftime("%a, %d %b"),
                font=("Arial", 10, "bold"), bg="#F8FAFC",
                fg=self.NAVY, width=13, anchor="w"
            ).pack(side="left")

            icon_label = tk.Label(row, bg="#F8FAFC")
            icon_label.pack(side="left", padx=10)
            self.set_weather_icon(
                icon_label, representative["icon"], size=(58, 58)
            )

            tk.Label(
                row, text=representative["description"],
                font=("Arial", 9), bg="#F8FAFC", fg=self.MUTED,
                width=20, anchor="w"
            ).pack(side="left", padx=5)

            low = self.temperature_text(min(temps))
            high = self.temperature_text(max(temps))
            tk.Label(
                row, text=f"{low}  /  {high}",
                font=("Arial", 10, "bold"), bg="#F8FAFC",
                fg=self.NAVY
            ).pack(side="right", padx=8)
        self.daily_container.update_idletasks()

        print("\n--- DAILY FORECAST DEBUG ---")
        print("Forecast dates:", dates)
        print("Rows created:", len(self.daily_container.winfo_children()))
        print(
            "Container size:",
            self.daily_container.winfo_width(),
            "x",
            self.daily_container.winfo_height()
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
