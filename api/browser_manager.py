import os
import sys
import asyncio
import subprocess
import config

async def ensure_local_browsers(add_log_func):
    """Checks and installs local Playwright browsers if needed."""
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            if sys.platform == "linux":
                await p.firefox.launch(headless=True)
            else:
                await p.chromium.launch(headless=True)
    except Exception as e:
        err_str = str(e)
        if "Executable doesn't exist" in err_str or "Please run the following command" in err_str:
            add_log_func("Playwright browsers missing. Installing...", "warning")
            subprocess.run([sys.executable, "-m", "playwright", "install", "firefox" if sys.platform == "linux" else "chromium"], check=True)
            add_log_func("Browsers installed successfully.", "system")
        elif "Host system is missing dependencies" in err_str or "Missing libraries" in err_str:
            add_log_func("Missing system libraries. Local launch will likely fail.", "error")
            raise e
        else:
            raise e

async def get_browser_context(p, session_dir, add_log_func):
    """Returns a browser context (local or remote)."""
    is_linux = sys.platform == "linux"
    browser_type = p.firefox if is_linux else p.chromium
    
    common_args = {
        "viewport": {'width': 1920, 'height': 1080},
        "color_scheme": 'dark',
        "user_agent": "Mozilla/5.0 (Linux; Android 13; V2202 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36",
        "permissions": ["geolocation", "notifications", "clipboard-read", "clipboard-write"],
    }

    # REMOTE CONNECTION
    if hasattr(config, "BROWSER_WS_URL") and config.BROWSER_WS_URL:
        remote_url = config.BROWSER_WS_URL.strip()
        add_log_func(f"Connecting to remote browser: {remote_url[:30]}...", "system")
        browser = await browser_type.connect(remote_url, timeout=60000)
        return await browser.new_context(**common_args)
    
    # LOCAL CONNECTION
    add_log_func("Launching local browser...", "system")
    await ensure_local_browsers(add_log_func)
    
    launch_args = {
        "user_data_dir": session_dir,
        "headless": True,
        **common_args
    }
    
    if not is_linux:
        launch_args.update({
            "channel": "chrome",
            "is_mobile": True,
            "has_touch": True,
            "device_scale_factor": 1,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--force-dark-mode"
            ]
        })
    else:
        launch_args["args"] = ["--force-dark-mode"]
        
    return await browser_type.launch_persistent_context(**launch_args)
