import customtkinter as ctk
import requests, time, random, threading
import itertools
import tkinter as tk
import ctypes
from tkinter import filedialog, messagebox
from tkinter import colorchooser

API_KEY = 'INPUT YOUR KEY' # https://vpnapi.io/ FREE API KEY

global_embed_title = ""
global_embed_gif_url = ""
is_bold = False
is_italic = False


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        return []

def save_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def open_file_in_editor(root, file_path):
    root.attributes("-topmost", False)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    
    editor_window = ctk.CTkToplevel()
    editor_window.title("Datei bearbeiten")
    editor_window.geometry("600x400")
    
    editor_text = ctk.CTkTextbox(editor_window)
    editor_text.pack(expand=True, fill="both")
    editor_text.insert(ctk.END, file_content)
    
    def save_and_close():
        content = editor_text.get("1.0", ctk.END)
        save_file(file_path, content)
        editor_window.destroy()
        root.attributes("-topmost", True)

    save_button = ctk.CTkButton(editor_window, text="Speichern und Schließen", command=save_and_close)
    save_button.pack(pady=10)

def check_webhooks_threaded(webhook_entry, status_label):
    def check_webhooks():
        file_path = webhook_entry.get()
        webhooks = read_file(file_path)

        if not webhooks:
            status_label.configure(text="[ERROR] Fehler: Keine Webhooks gefunden!", text_color="red")
            return

        valid_webhooks = []
        invalid_webhooks = 0
        total_webhooks = len(webhooks)

        def update_status_label(valid_count, checked_count, invalid_count):
            """Update the status label with the number of checked and valid webhooks."""
            status_label.configure(
                text=f"{checked_count} / {total_webhooks} Webhooks überprüft. "
                     f"{valid_count} gültig, {invalid_count} ungültig.",
                text_color="red" if invalid_count > 0 else "green"
            )

        update_status_label(0, 0, 0)

        for checked_count, webhook in enumerate(webhooks, start=1):
            try:
                response = requests.get(webhook, timeout=5)
                if response.status_code >= 200 and response.status_code < 300:
                    valid_webhooks.append(webhook)
                else:
                    invalid_webhooks += 1
            except requests.exceptions.RequestException:
                invalid_webhooks += 1

            valid_count = len(valid_webhooks)
            checked_count = checked_count  
            status_label.after(0, update_status_label, valid_count, checked_count, invalid_webhooks)

        save_file(file_path, "\n".join(valid_webhooks))

        update_status_label(len(valid_webhooks), total_webhooks, invalid_webhooks)

    check_thread = threading.Thread(target=check_webhooks)
    check_thread.start()

def on_check_webhooks(webhook_entry, status_label):
    check_webhooks_threaded(webhook_entry, status_label)

def send_message_to_webhook(webhook_url, message, repeat, delay, progress_label, progress_bar, status_label, total, current_count, random_delay_enabled, log_widget, title, gif_url):
    content_message = "||@everyone @here||"
    embed = {
        "title": title,                   # Titel aus Eingabefeld
        "description": message,           # Nachricht aus der .txt         
        "color": 5814783,                 # Hex-Farbe in Dezimal: #58D3F7
        "image": {
            "url": gif_url                # GIF-URL aus Eingabefeld
        }
    }

    success = True
    for _ in range(repeat):
        try:
            payload = {"content": content_message, "embeds": [embed]}
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 204:
                success = False
                break
        except requests.exceptions.RequestException as e:
            success = False
            break
        
        if random_delay_enabled:
            delay = random.uniform(0.5, 9.59)  
        time.sleep(delay)

    current_count[0] += 1
    progress_label.configure(text=f"{current_count[0]}/{total} Webhooks gesendet")
    progress_bar.set(current_count[0] / total)

    if success:
        add_to_log(log_widget, f"[SUCCESS] Erfolgreich an Webhook gesendet: {webhook_url}", success=True)
        status_label.configure(text="[SUCCESS] Alle Nachrichten erfolgreich gesendet!", text_color="green")
    else:
        add_to_log(log_widget, f"[ERROR] Fehler beim Senden an Webhook: {webhook_url}", success=False)
        status_label.configure(text=f"[ERROR] Fehler beim Senden an Webhook: {webhook_url}", text_color="red")

    progress_label.update()
    status_label.update()

def send_messages_threaded(title, gif_url, webhooks, message, repeat, delay, progress_label, progress_bar, status_label, random_delay_enabled, log_widget):
    total = len(webhooks)
    current_count = [0]  

    for webhook in webhooks:
        send_message_to_webhook(
            webhook, message, repeat, delay, progress_label, progress_bar, 
            status_label, total, current_count, random_delay_enabled, log_widget, title, gif_url
        )

def send_messages(webhooks, message, repeat, delay, progress_label, progress_bar, status_label, random_delay_enabled):
    total = len(webhooks)
    current_count = [0]  

    for webhook in webhooks:
        send_message_to_webhook(webhook, message, repeat, delay, progress_label, progress_bar, status_label, total, current_count, random_delay_enabled)

def load_file(entry):
    file_path = filedialog.askopenfilename()
    if file_path:
        entry.delete(0, ctk.END)
        entry.insert(0, file_path)

def preview_files(webhook_entry, message_entry, webhook_preview, message_preview):
    webhooks = read_file(webhook_entry.get())
    message_lines = read_file(message_entry.get())

    if webhooks:
        webhook_preview.configure(state="normal")
        webhook_preview.delete(1.0, ctk.END)
        webhook_preview.insert(ctk.END, "\n".join(webhooks))
        webhook_preview.configure(state="disabled")

    if message_lines:
        message_preview.configure(state="normal")
        message_preview.delete(1.0, ctk.END)
        message_preview.insert(ctk.END, "\n".join(message_lines))
        message_preview.configure(state="disabled")

def on_send(webhook_entry, message_entry, repeat_entry, delay_entry, progress_label, progress_bar, status_label, random_delay_enabled, log_widget):
    webhooks = read_file(webhook_entry.get())
    messages = read_file(message_entry.get())

    if not webhooks:
        status_label.configure(text="[ERROR] : Keine Webhooks gefunden!", text_color="red")
        return

    if not messages:
        status_label.configure(text="[ERROR] Fehler: Keine Nachricht gefunden!", text_color="red")
        return

    try:
        repeat = int(repeat_entry.get())
        delay = float(delay_entry.get())
        if repeat < 1 or delay < 0:
            raise ValueError
    except ValueError:
        status_label.configure(text="[ERROR] Fehler: Ungültige Eingaben!", text_color="red")
        return

    title = global_embed_title if global_embed_title else webhooks[0]  
    gif_url = global_embed_gif_url if global_embed_gif_url else "https://porngif.co/wp-content/uploads/2024/12/porngif-34aaa5bee507e01143261b2ade71d278.gif"  

    if global_embed_title and global_embed_gif_url:
        message = f"{title}\n {gif_url}\n"
    else:
        message = "\n".join(messages)

    progress_label.configure(text=f"0/{len(webhooks)} Webhooks gesendet")
    progress_bar.set(0)

    send_thread = threading.Thread(target=send_messages_threaded, args=(
        title, gif_url, webhooks, message, repeat, delay, progress_label, progress_bar, status_label, random_delay_enabled, log_widget
    ))
    send_thread.start()

def interpolate_color(color1, color2, factor):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return r, g, b

def rgb_to_hex(rgb):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

def change_color(header, colors, current_index, factor):
    next_index = (current_index + 1) % len(colors)
    
    color1 = colors[current_index]
    color2 = colors[next_index]
    interpolated_color = interpolate_color(color1, color2, factor)
    
    header.configure(fg_color=rgb_to_hex(interpolated_color))
    
    if factor < 1.0:
        factor += 0.05  
        header.after(30, change_color, header, colors, current_index, factor)  
    else:
        header.after(500, change_color, header, colors, next_index, 0)  

def add_to_log(log_widget, message, success=True):
    color = "green" if success else "red"
    log_widget.configure(state="normal")

    current_index = log_widget.index(ctk.END).split(".")
    current_line = int(current_index[0]) - 1  
    start_index = f"{current_line}.0"        
    end_index = f"{current_line + 1}.0"      

    log_widget.insert(ctk.END, f"{message}\n")

    log_widget.tag_add(color, start_index, end_index)
    log_widget.tag_config(color, foreground=color)

    log_widget.configure(state="disabled")
    
    if hasattr(log_widget, 'update_log'):
        log_widget.update_log()

def get_ip_and_vpn_status():
    try:
        ip_response = requests.get('https://api.ipify.org')  
        ip = ip_response.text

        vpn_check_url = f'https://vpnapi.io/api/{ip}?key={API_KEY}'
        vpn_response = requests.get(vpn_check_url)
        vpn_data = vpn_response.json()
        is_vpn = vpn_data.get('security', {}).get('vpn', False)
        
        return ip, is_vpn
    except requests.RequestException:
        return "IP nicht verfügbar", False

def update_ip_label(ip_label, vpn_label):
    def refresh():
        while True:
            try:
                ip, is_vpn = get_ip_and_vpn_status()
                ip_label.after(0, lambda: ip_label.configure(text=f"IP-Adresse: {ip}"))
                if is_vpn:
                    ip_label.after(0, lambda: ip_label.configure(text_color="green"))
                    vpn_label.after(0, lambda: vpn_label.configure(text="VPN aktiviert", text_color="green"))
                else:
                    ip_label.after(0, lambda: ip_label.configure(text_color="red"))
                    vpn_label.after(0, lambda: vpn_label.configure(text="Kein VPN", text_color="red"))
            except Exception as e:
                print(f"Fehler beim Abrufen der IP: {e}")
            threading.Event().wait(600)  
    threading.Thread(target=refresh, daemon=True).start()

def manual_refresh(ip_label, vpn_label):
    def refresh():
        try:
            ip, is_vpn = get_ip_and_vpn_status()
            ip_label.configure(text=f"IP-Adresse: {ip}")
            if is_vpn:
                ip_label.configure(text_color="green")
                vpn_label.configure(text="VPN aktiviert", text_color="green")
            else:
                ip_label.configure(text_color="red")
                vpn_label.configure(text="Kein VPN", text_color="red")
        except Exception as e:
            print(f"Fehler beim manuellen Aktualisieren der IP: {e}")
    threading.Thread(target=refresh, daemon=True).start()

####### GUI #######
def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Hayat Nigger")
    root.geometry("950x750")
    #root.protocol("WM_DELETE_WINDOW", on_close)
    
    root.attributes("-topmost", True)    
    
    root.overrideredirect(True)

    # Regenbogenfarben in RGB
    rainbow_colors = [
        (255, 0, 0),     # Red
        (255, 127, 0),   # Orange
        (255, 255, 0),   # Yellow
        (0, 255, 0),     # Green
        (0, 0, 255),     # Blue
        (75, 0, 130),    # Indigo
        (238, 130, 238)  # Violet
    ]

    header = ctk.CTkFrame(root, height=30, fg_color=rgb_to_hex(rainbow_colors[0]))  
    header.pack(fill="x", side="top")

    maximize_button = ctk.CTkButton(header, text="☐", width=30, height=30, command=lambda: root.state("zoomed" if root.state() == "normal" else "normal"))
    maximize_button.pack(side="right", padx=5)

    close_button = ctk.CTkButton(header, text="X", width=30, height=30, command=root.destroy)
    close_button.pack(side="right", padx=5)

    def on_press(event):
        global offset_x, offset_y
        offset_x = event.x
        offset_y = event.y

    def on_move(event):
        delta_x = event.x - offset_x
        delta_y = event.y - offset_y
        new_x = root.winfo_x() + delta_x
        new_y = root.winfo_y() + delta_y
        root.geometry(f"+{new_x}+{new_y}")

    header.bind("<Button-1>", on_press)
    header.bind("<B1-Motion>", on_move)

    tabview = ctk.CTkTabview(root, width=400)
    tabview.pack(fill="both", expand=True, padx=10, pady=10)

    main_tab = tabview.add("Main")
    embedsettings_tab = tabview.add("Embed Preview..")
    settings_tab = tabview.add("Design")
    check_tab = tabview.add("Webhook-Überprüfung")
    log_tab = tabview.add("DEV LOG")    
    ip_tab = tabview.add("IP")


    ip_label = ctk.CTkLabel(ip_tab, text="IP-Adresse: Lade...")
    ip_label.pack(pady=20)

    vpn_label = ctk.CTkLabel(ip_tab, text="Kein VPN", text_color="red")
    vpn_label.pack(pady=10)

    refresh_button = ctk.CTkButton(ip_tab, text="IP manuell aktualisieren", command=lambda: manual_refresh(ip_label, vpn_label))
    refresh_button.pack(pady=10)
    
    update_ip_label(ip_label, vpn_label)


    #log_textbox = ctk.CTkTextbox(log_tab, state="normal", height=400)
    #log_textbox.pack(expand=True, fill="both")    
    log_widget = ctk.CTkTextbox(log_tab, width=870, height=550)
    log_widget.grid(row=10, column=0, columnspan=2, pady=10)


    main_tab.grid_rowconfigure(0, weight=1)
    main_tab.grid_rowconfigure(1, weight=1)
    main_tab.grid_rowconfigure(2, weight=3)
    main_tab.grid_rowconfigure(3, weight=3)
    main_tab.grid_rowconfigure(4, weight=1)
    main_tab.grid_rowconfigure(5, weight=1)
    main_tab.grid_rowconfigure(6, weight=1)
    main_tab.grid_rowconfigure(7, weight=1)
    main_tab.grid_rowconfigure(8, weight=1)
    main_tab.grid_rowconfigure(9, weight=1)
    main_tab.grid_rowconfigure(10, weight=1)

    main_tab.grid_columnconfigure(0, weight=1)
    main_tab.grid_columnconfigure(1, weight=3)
    main_tab.grid_columnconfigure(2, weight=1)
    
    check_tab.grid_rowconfigure(0, weight=0)  
    check_tab.grid_rowconfigure(1, weight=0)  
    check_tab.grid_rowconfigure(2, weight=0)  
    check_tab.grid_rowconfigure(3, weight=0)  

    check_tab.grid_columnconfigure(0, weight=1)  
    check_tab.grid_columnconfigure(1, weight=3)  
    check_tab.grid_columnconfigure(2, weight=0) 
 

    ctk.CTkLabel(main_tab, text="Webhook-Datei:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    webhook_entry = ctk.CTkEntry(main_tab)
    webhook_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    ctk.CTkButton(main_tab, text="Durchsuchen", width=100, command=lambda: load_file(webhook_entry)).grid(row=0, column=2, padx=10, pady=10)
    ctk.CTkButton(main_tab, text="Bearbeiten", width=100, command=lambda: open_file_in_editor(root, webhook_entry.get())).grid(row=0, column=3, padx=10, pady=10)

    ctk.CTkLabel(main_tab, text="Nachricht-Datei:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    message_entry = ctk.CTkEntry(main_tab)
    message_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    ctk.CTkButton(main_tab, text="Durchsuchen", width=100, command=lambda: load_file(message_entry)).grid(row=1, column=2, padx=10, pady=10)
    ctk.CTkButton(main_tab, text="Bearbeiten", width=100, command=lambda: open_file_in_editor(root, message_entry.get())).grid(row=1, column=3, padx=10, pady=10)


    embed_frame = ctk.CTkFrame(embedsettings_tab)
    embed_frame.grid(row=11, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(embed_frame, text="Titel:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    title_entry = ctk.CTkEntry(embed_frame, width=250)
    title_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ctk.CTkLabel(embed_frame, text="GIF-URL:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    gif_entry = ctk.CTkEntry(embed_frame, width=250)
    gif_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    def test_embed():
        global global_embed_title, global_embed_gif_url
        title = title_entry.get()
        gif_url = gif_entry.get()

        if not title or not gif_url:
            status_label.configure(text="Fehler: Bitte Titel und GIF-URL eingeben.", text_color="red")
        else:
            global_embed_title = title
            global_embed_gif_url = gif_url

            embed_preview.configure(state="normal")
            embed_preview.delete(1.0, "end")
            embed_preview.insert("end", f"**Titel:** {title}\n**GIF-URL:** {gif_url}\n")
            embed_preview.insert("end", f"![GIF]({gif_url})")  
            embed_preview.configure(state="disabled")
            status_label.configure(text="Embed-Vorschau aktualisiert.", text_color="green")

    test_button = ctk.CTkButton(embed_frame, text="Embed testen", command=test_embed)
    test_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")

    status_label = ctk.CTkLabel(embedsettings_tab, text="", text_color="green")
    status_label.grid(row=12, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    embed_preview = ctk.CTkTextbox(embedsettings_tab, state="disabled", height=150)
    embed_preview.grid(row=13, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    font_size_label = ctk.CTkLabel(embed_frame, text="Schriftgröße (Titel):")
    font_size_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    font_size_slider = ctk.CTkSlider(embed_frame, from_=8, to=24, number_of_steps=16)
    font_size_slider.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def update_font_size(font_size):
        title = title_entry.get()
        gif_url = gif_entry.get()
        if title and gif_url:
            embed_preview.configure(state="normal")
            embed_preview.delete(1.0, "end")
            embed_preview.insert("end", f"**Titel:** {title}\n**GIF-URL:** {gif_url}\n")
            embed_preview.insert("end", f"![GIF]({gif_url})")  
            embed_preview.configure(state="disabled")

            embed_preview.configure(font=("Arial", int(font_size)))  
        else:
            status_label.configure(text="Fehler: Bitte Titel und GIF-URL eingeben.", text_color="red")

    font_size_slider.configure(command=update_font_size)

    bold_button = ctk.CTkButton(embed_frame, text="Fett", command=lambda: toggle_bold())
    bold_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

    italic_button = ctk.CTkButton(embed_frame, text="Kursiv", command=lambda: toggle_italic())
    italic_button.grid(row=2, column=1, padx=5, pady=5, sticky="w")


    def toggle_bold():
        global is_bold
        is_bold = not is_bold
        update_font_style()

    def toggle_italic():
        global is_italic
        is_italic = not is_italic
        update_font_style()

    def update_font_style():
        title = title_entry.get()
        gif_url = gif_entry.get()
        if title and gif_url:
            embed_preview.configure(state="normal")
            embed_preview.delete(1.0, "end")
            embed_preview.insert("end", f"**Titel:** {title}\n**GIF-URL:** {gif_url}\n")
            embed_preview.insert("end", f"![GIF]({gif_url})")

            font_style = "normal"
            if is_bold:
                font_style = "bold"
            if is_italic:
                font_style = "italic" if font_style == "normal" else f"{font_style} italic"

            embed_preview.configure(font=("Arial", int(font_size_slider.get()), font_style))  
            embed_preview.configure(state="disabled")

    def choose_text_color():
        color_code = colorchooser.askcolor(title="Wählen Sie eine Textfarbe")[1]
        if color_code:
            update_text_color(color_code)

    color_button = ctk.CTkButton(embed_frame, text="Textfarbe", command=choose_text_color)
    color_button.grid(row=3, column=0, padx=5, pady=5, sticky="w")

    def update_text_color(color):
        title = title_entry.get()
        gif_url = gif_entry.get()
        if title and gif_url:
            embed_preview.configure(state="normal")
            embed_preview.delete(1.0, "end")
            embed_preview.insert("end", f"**Titel:** {title}\n**GIF-URL:** {gif_url}\n")
            embed_preview.insert("end", f"![GIF]({gif_url})")
            embed_preview.configure(fg_color=color) 
            embed_preview.configure(state="disabled")

    def choose_bg_color():
        color_code = colorchooser.askcolor(title="Wählen Sie eine Hintergrundfarbe")[1]
        if color_code:
            update_bg_color(color_code)

    bg_color_button = ctk.CTkButton(embed_frame, text="Hintergrundfarbe", command=choose_bg_color)
    bg_color_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")

    def update_bg_color(color):
        embed_preview.configure(bg_color=color)  

    def reset_embed():
        title_entry.delete(0, "end")
        gif_entry.delete(0, "end")
        embed_preview.configure(state="normal")
        embed_preview.delete(1.0, "end")
        embed_preview.configure(state="disabled")
        status_label.configure(text="", text_color="green")

    reset_button = ctk.CTkButton(embed_frame, text="Zurücksetzen", command=reset_embed)
    reset_button.grid(row=5, column=0, padx=5, pady=5, sticky="w")


    ctk.CTkLabel(main_tab, text="Webhooks Vorschau:").grid(row=2, column=0, padx=10, pady=10, sticky="ne")
    webhook_preview = ctk.CTkTextbox(main_tab, state="disabled", height=100)
    webhook_preview.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(main_tab, text="Nachricht Vorschau:").grid(row=3, column=0, padx=10, pady=10, sticky="ne")
    message_preview = ctk.CTkTextbox(main_tab, state="disabled", height=100)
    message_preview.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    ctk.CTkButton(main_tab, text="Vorschau aktualisieren", command=lambda: preview_files(webhook_entry, message_entry, webhook_preview, message_preview)).grid(row=4, column=1, padx=10, pady=10)

    ctk.CTkLabel(main_tab, text="Wiederholungsanzahl:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
    repeat_entry = ctk.CTkEntry(main_tab)
    repeat_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
    repeat_entry.insert(0, "1")

    ctk.CTkLabel(main_tab, text="Verzögerung (Sekunden):").grid(row=6, column=0, padx=10, pady=10, sticky="e")
    delay_entry = ctk.CTkEntry(main_tab)
    delay_entry.grid(row=6, column=1, padx=10, pady=10, sticky="w")
    delay_entry.insert(0, "0.5")

    delay_value_label = ctk.CTkLabel(main_tab, text="Aktuelle Verzögerung: 0.5s")
    delay_value_label.grid(row=7, column=0, padx=10, pady=10, sticky="e")
    
    def update_delay_label():
        if random_delay_switch.get():
            delay_value_label.configure(text=f"Aktuelle Verzögerung: {random.uniform(0.5, 9.59):.2f}s")
        else:
            delay_value_label.configure(text=f"Aktuelle Verzögerung: {delay_entry.get()}s")

        global after_id
        if 'after_id' in globals():
            delay_value_label.after_cancel(after_id)

        after_id = delay_value_label.after(350, update_delay_label)

    after_id = None

    random_delay_switch = ctk.CTkSwitch(main_tab, text="Zufällige Verzögerung aktivieren", command=update_delay_label)
    random_delay_switch.grid(row=7, column=1, pady=10)

    progress_label = ctk.CTkLabel(main_tab, text="0/0 Webhooks gesendet")
    progress_label.grid(row=8, column=1, pady=10)

    progress_bar = ctk.CTkProgressBar(main_tab)
    progress_bar.grid(row=9, column=1, pady=10, sticky="ew")

    status_label = ctk.CTkLabel(main_tab, text="", text_color="white")
    status_label.grid(row=10, column=1, pady=10)

    ctk.CTkButton(
        main_tab, 
        text="Senden", 
        width=150, 
        height=40, 
        command=lambda: on_send(
            webhook_entry, 
            message_entry, 
            repeat_entry, 
            delay_entry, 
            progress_label, 
            progress_bar, 
            status_label, 
            random_delay_switch.get(), 
            log_widget 
        )
    ).grid(row=11, column=1, pady=10)

    ctk.CTkLabel(check_tab, text="Webhook-Datei überprüfen:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
    webhook_entry_check = ctk.CTkEntry(check_tab)
    webhook_entry_check.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(check_tab, text="Durchsuchen", command=lambda: load_file(webhook_entry_check)).grid(row=1, column=2, padx=5, pady=5)
    status_label = ctk.CTkLabel(check_tab, text="", text_color="white")
    status_label.grid(row=2, column=1, pady=5, sticky="w")
    ctk.CTkButton(check_tab, text="Webhooks überprüfen", width=80, height=40, 
                command=lambda: on_check_webhooks(webhook_entry_check, status_label)).grid(row=3, column=1, pady=5, sticky="nsew")

    def clear_log(log_widget):
        log_widget.configure(state="normal")
        log_widget.delete(1.0, ctk.END)
        log_widget.configure(state="disabled")

    def save_log_to_file(log_widget):
        log_content = log_widget.get(1.0, ctk.END)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textdateien", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(log_content)

    def open_log_window(log_widget):
        log_window = ctk.CTkToplevel()
        log_window.title("DEV Log")
        log_window.geometry("650x800")

        log_window.attributes("-topmost", True)
        log_window.overrideredirect(True)

        rainbow_colors = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (75, 0, 130),    # Indigo
            (238, 130, 238)  # Violet
        ]

        header2 = ctk.CTkFrame(log_window, height=30, fg_color=rgb_to_hex(rainbow_colors[0]))
        header2.grid(row=0, column=0, columnspan=3, sticky="ew")

        maximize_button = ctk.CTkButton(header2, text="☐", width=30, height=30, command=lambda: log_window.state("zoomed" if log_window.state() == "normal" else "normal"))
        maximize_button.grid(row=0, column=1, padx=5, sticky="e")

        close_button = ctk.CTkButton(header2, text="X", width=30, height=30, command=log_window.destroy)
        close_button.grid(row=0, column=2, padx=5, sticky="e")
        
        log_textbox = ctk.CTkTextbox(log_window, state="normal")
        log_textbox.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        log_textbox.insert(ctk.END, log_widget.get(1.0, ctk.END))
        log_textbox.configure(state="disabled")

        def on_press(event):
            global offset_x, offset_y
            offset_x = event.x
            offset_y = event.y

        def on_move(event):
            delta_x = event.x - offset_x
            delta_y = event.y - offset_y
            new_x = log_window.winfo_x() + delta_x
            new_y = log_window.winfo_y() + delta_y
            log_window.geometry(f"+{new_x}+{new_y}")

        header2.bind("<Button-1>", on_press)
        header2.bind("<B1-Motion>", on_move)

        def update_log():
            log_textbox.configure(state="normal")
            log_textbox.delete(1.0, ctk.END)  
            log_textbox.insert(ctk.END, log_widget.get(1.0, ctk.END))  
            log_textbox.configure(state="disabled")

        def refresh_log():
            update_log()
            log_window.after(4500, refresh_log)

        def search_log():
            search_term = search_entry.get()
            if search_term:
                log_text = log_widget.get(1.0, "end-1c")
                results = []
                for line in log_text.split("\n"):
                    if search_term.lower() in line.lower():
                        results.append(line)
                log_widget.delete(1.0, "end")
                log_widget.insert("1.0", "\n".join(results))

        def filter_log():
            log_text = log_widget.get(1.0, "end-1c")  
            filtered_logs = []  

            if all_level_var.get():
                filtered_logs = log_text.split("\n")  
            else:
                for line in log_text.split("\n"):  
                    if info_var.get() and "INFO" in line:
                        filtered_logs.append(line)
                    if warn_var.get() and "WARN" in line:
                        filtered_logs.append(line)
                    if error_var.get() and "ERROR" in line:
                        filtered_logs.append(line)

            log_textbox.configure(state="normal")
            log_textbox.delete(1.0, ctk.END)
            log_textbox.insert(1.0, "\n".join(filtered_logs))
            log_textbox.configure(state="disabled")

        refresh_log()

        ctk.CTkButton(log_window, text="Log speichern", command=lambda: save_log_to_file(log_widget)).grid(row=2, column=0, padx=5, pady=10)
        ctk.CTkButton(log_window, text="Log löschen", command=lambda: clear_log(log_widget)).grid(row=2, column=1, padx=5, pady=10)

        search_label = ctk.CTkLabel(log_window, text="Search Log:")
        search_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        search_entry = ctk.CTkEntry(log_window)
        search_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        search_button = ctk.CTkButton(log_window, text="Search", command=search_log)
        search_button.grid(row=3, column=2, padx=5, pady=5)

        log_level_label = ctk.CTkLabel(log_window, text="(TESTING) Log Level:")
        log_level_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        all_level_var = ctk.BooleanVar(value=True)  
        all_level_checkbox = ctk.CTkCheckBox(log_window, text="All", variable=all_level_var)
        all_level_checkbox.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        info_var = ctk.BooleanVar(value=False)  
        info_checkbox = ctk.CTkCheckBox(log_window, text="INFO", variable=info_var)
        info_checkbox.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        warn_var = ctk.BooleanVar(value=False)  
        warn_checkbox = ctk.CTkCheckBox(log_window, text="WARN", variable=warn_var)
        warn_checkbox.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        error_var = ctk.BooleanVar(value=False)  
        error_checkbox = ctk.CTkCheckBox(log_window, text="ERROR", variable=error_var)
        error_checkbox.grid(row=7, column=1, padx=5, pady=5, sticky="w")

        apply_filter_button = ctk.CTkButton(log_window, text="Filter anwenden", command=filter_log)
        apply_filter_button.grid(row=8, column=1, padx=5, pady=10, sticky="ew")


        log_window.grid_rowconfigure(1, weight=1)
        log_window.grid_columnconfigure(0, weight=1)
        log_window.grid_columnconfigure(1, weight=1)
        log_window.grid_columnconfigure(2, weight=1)

        change_color(header2, rainbow_colors, 0, 0)


    log_tab.grid_rowconfigure(0, weight=1)  
    log_tab.grid_rowconfigure(12, weight=0)  
    log_tab.grid_columnconfigure(0, weight=0)  
    ctk.CTkButton(log_tab, text="(TESTING) Log öffnen", command=lambda: open_log_window(log_widget)).grid(row=12, column=0, pady=10, sticky="w")

    def change_cursor(cursor_style):
        root.config(cursor=cursor_style)

    ctk.CTkLabel(settings_tab, text="Design ändern:").pack(pady=20)

    ctk.CTkButton(settings_tab, text="Hell", command=lambda: ctk.set_appearance_mode("light")).pack(pady=10)
    ctk.CTkButton(settings_tab, text="Dunkel", command=lambda: ctk.set_appearance_mode("dark")).pack(pady=10)

    ctk.CTkLabel(settings_tab, text="Wähle einen Cursor:").pack(pady=20)
    cursor_options = ["arrow", "circle", "cross", "hand2", "watch"]  
    cursor_dropdown = ctk.CTkOptionMenu(settings_tab, values=cursor_options, command=change_cursor)
    cursor_dropdown.pack(pady=10)
    cursor_dropdown.set("arrow")  

    change_color(header, rainbow_colors, 0, 0)

    root.mainloop()

if __name__ == '__main__':
    print("Starting GUI...")
    main()
