import tkinter as tk
root = tk.Tk()
root.withdraw()
from mayan_miner.app import MayanMinerApp
from mayan_miner.config import SecureConfigManager
config = SecureConfigManager().load_config()
app = MayanMinerApp(root, initial_config=config, start_minimized=False)
root.deiconify()
root.update()
print("Initial tab:", app._active_tab)
app._show_tab("settings")
root.update()
print("After settings click:", app._active_tab)
app._show_tab("dashboard")
root.update()
print("After dashboard click:", app._active_tab)
print("Dashboard visible:", app.dashboard_frame.winfo_ismapped())
print("Settings visible:", app.settings_frame.winfo_ismapped())
for key, btn in app.nav_buttons.items():
    print("Nav btn", key, "style:", btn.cget("style"))
root.destroy()
print("SUCCESS")
