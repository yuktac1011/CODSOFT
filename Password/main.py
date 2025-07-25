import secrets
import string
from nicegui import ui, app

# --- Password Generation and Cracking Logic (Backend) ---

def generate_password(length, use_upper, use_lower, use_digits, use_special):
    """Generates a secure password based on specified criteria."""
    pool, password_chars = '', []
    
    # Build the character pool and ensure at least one of each required type
    if use_upper:
        pool += string.ascii_uppercase
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if use_lower:
        pool += string.ascii_lowercase
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if use_digits:
        pool += string.digits
        password_chars.append(secrets.choice(string.digits))
    if use_special:
        pool += string.punctuation
        password_chars.append(secrets.choice(string.punctuation))
        
    if not pool:
        return "Error: Select at least one character type."

    # Fill the rest of the password length
    remaining_length = length - len(password_chars)
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(pool))

    secrets.SystemRandom().shuffle(password_chars)
    return ''.join(password_chars)

def password_cracker(password):
    """Estimates the time to crack a password via brute-force."""
    if not password or "Error" in password:
        return {"text": "N/A", "color": "text-gray-500"}
        
    char_set_size = sum([
        26 if any(c.islower() for c in password) else 0,
        26 if any(c.isupper() for c in password) else 0,
        10 if any(c.isdigit() for c in password) else 0,
        32 if any(c in string.punctuation for c in password) else 0
    ])

    if char_set_size == 0:
        return {"text": "Analysis unavailable.", "color": "text-gray-500"}
    
    try:
        combinations = char_set_size ** len(password)
        guesses_per_second = 10**10
        seconds_to_crack = combinations / guesses_per_second
    except OverflowError:
        return {"text": "Astronomically Strong", "color": "text-green-500"}

    if seconds_to_crack < 60:
        return {"text": "Very Weak (< 1 min)", "color": "text-red-500"}
    elif seconds_to_crack < 3600:
        return {"text": f"Weak (~{seconds_to_crack/60:.0f} mins)", "color": "text-orange-500"}
    elif seconds_to_crack < 86400 * 30:
        return {"text": f"Moderate (~{seconds_to_crack/3600:.1f} hrs)", "color": "text-yellow-500"}
    elif seconds_to_crack < 31536000:
        return {"text": f"Strong (~{seconds_to_crack/86400:.1f} days)", "color": "text-lime-500"}
    else:
        years = seconds_to_crack / 31536000
        return {"text": f"Very Strong (~{years:,.1f} yrs)", "color": "text-green-500"}

# --- User Interface Definition (Frontend) ---

@ui.page('/')
def main_page():
    # --- UI State and Styling ---
    app.storage.user.update({
        'level': app.storage.user.get('level', 'Hard'), # New state for levels
        'length': app.storage.user.get('length', 18),
        'use_upper': app.storage.user.get('use_upper', True),
        'use_lower': app.storage.user.get('use_lower', True),
        'use_digits': app.storage.user.get('use_digits', True),
        'use_special': app.storage.user.get('use_special', True),
    })
    
    ui.query('body').classes('bg-gray-100 dark:bg-gray-900')

    # --- Header ---
    with ui.row().classes('w-full p-4 items-center justify-between'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('password', size='lg', color='primary')
            ui.label('Secure Password Suite').classes('text-2xl font-bold text-gray-800 dark:text-gray-200')
        dark_mode = ui.dark_mode()
        ui.switch(text='Dark Mode').bind_value(dark_mode, 'value')

    # --- Main Content Column ---
    with ui.column().classes('w-full max-w-2xl mx-auto p-4 items-center gap-6'):
        
        # --- Settings Card ---
        with ui.card().classes('w-full rounded-2xl shadow-md dark:bg-gray-800'):
            ui.label('1. Choose Your Strength').classes('text-xl font-semibold text-gray-700 dark:text-gray-300')
            
            # Level Selection
            level_options = {'Easy': 'Easy', 'Medium': 'Medium', 'Hard': 'Hard', 'Custom': 'Custom'}
            level_radio = ui.radio(level_options, value='Hard').bind_value(app.storage.user, 'level').props('inline')
            
            ui.separator().classes('my-4')
            
            # Customization Section
            ui.label('2. Customize (If Applicable)').classes('text-xl font-semibold text-gray-700 dark:text-gray-300')
            with ui.row().classes('w-full items-center mt-4'):
                ui.label('Length:').classes('text-lg text-gray-600 dark:text-gray-400')
                slider = ui.slider(min=4, max=50).bind_value(app.storage.user, 'length').classes('w-2/3')
                ui.label().bind_text_from(app.storage.user, 'length').classes('text-lg font-mono text-primary')
            with ui.grid(columns=2).classes('w-full gap-x-8 gap-y-2 pt-4 text-gray-600 dark:text-gray-400'):
                upper_switch = ui.switch('Uppercase (A-Z)').bind_value(app.storage.user, 'use_upper')
                lower_switch = ui.switch('Lowercase (a-z)').bind_value(app.storage.user, 'use_lower')
                digits_switch = ui.switch('Digits (0-9)').bind_value(app.storage.user, 'use_digits')
                special_switch = ui.switch('Special (!@#$)').bind_value(app.storage.user, 'use_special')

        # --- Result Card ---
        with ui.card().classes('w-full rounded-2xl shadow-md dark:bg-gray-800'):
            ui.label('3. Your Secure Password').classes('text-xl font-semibold text-gray-700 dark:text-gray-300')
            with ui.row().classes('w-full items-center bg-gray-100 dark:bg-gray-700 p-3 rounded-lg mt-4'):
                password_display = ui.label().classes('flex-grow text-center font-mono text-2xl break-all text-gray-800 dark:text-gray-200')
                copy_button = ui.button(icon='content_copy').props('flat round color=primary')
            with ui.row().classes('w-full items-center pt-4'):
                ui.label('Strength:').classes('text-lg font-semibold text-gray-600 dark:text-gray-400')
                strength_display = ui.label().classes('text-lg font-bold')
        
        # --- Save Card ---
        with ui.card().classes('w-full rounded-2xl shadow-md dark:bg-gray-800'):
            ui.label('4. Save Password').classes('text-xl font-semibold text-gray-700 dark:text-gray-300')
            with ui.row().classes('w-full items-center mt-4'):
                service_input = ui.input(placeholder='e.g., Google, Facebook...').classes('flex-grow')
                save_button = ui.button('Save to file', icon='save')

    # --- Functions that control UI and Logic ---

    def update_password():
        """Generate and update the password based on current state."""
        password = generate_password(
            app.storage.user['length'], app.storage.user['use_upper'], app.storage.user['use_lower'],
            app.storage.user['use_digits'], app.storage.user['use_special']
        )
        password_display.set_text(password)
        
        strength_info = password_cracker(password)
        strength_display.set_text(strength_info['text'])
        strength_display.classes(replace=f"text-lg font-bold {strength_info['color']}")

    def handle_level_change():
        """Update settings based on the selected level and regenerate password."""
        level = app.storage.user['level']
        
        presets = {
            'Easy':   {'len': 10, 'upper': True, 'lower': True, 'digits': False, 'special': False},
            'Medium': {'len': 14, 'upper': True, 'lower': True, 'digits': True, 'special': False},
            'Hard':   {'len': 18, 'upper': True, 'lower': True, 'digits': True, 'special': True},
        }

        if level == 'Custom':
            slider.enable()
            for switch in [upper_switch, lower_switch, digits_switch, special_switch]:
                switch.enable()
        else:
            slider.disable()
            for switch in [upper_switch, lower_switch, digits_switch, special_switch]:
                switch.disable()
            
            config = presets[level]
            app.storage.user.update({
                'length': config['len'],
                'use_upper': config['upper'],
                'use_lower': config['lower'],
                'use_digits': config['digits'],
                'use_special': config['special'],
            })
        
        update_password()

    def save_password():
        """Saves the service name and password to saved_passwords.txt."""
        service = service_input.value.strip()
        password = password_display.text
        if not service or not password or "Error" in password:
            ui.notify('Please enter a service name and generate a password first.', type='warning')
            return
        try:
            with open("saved_passwords.txt", "a", encoding="utf-8") as f:
                f.write(f"Service: {service}\nPassword: {password}\n" + "-"*30 + "\n")
            ui.notify(f"Password for '{service}' saved to saved_passwords.txt", type='positive')
            service_input.value = ''
        except IOError as e:
            ui.notify(f"Error saving file: {e}", type='negative')

    async def copy_to_clipboard():
        await ui.run_javascript(f'navigator.clipboard.writeText("{password_display.text}")')
        ui.notify('Password copied to clipboard!', type='info')

    # --- Link Functions to UI Events ---
    level_radio.on('change', handle_level_change)
    for component in [slider, upper_switch, lower_switch, digits_switch, special_switch]:
        component.on('change', update_password, throttle=0.2)
    save_button.on('click', save_password)
    copy_button.on('click', copy_to_clipboard)
    
    # --- Initial Setup ---
    handle_level_change()

# --- Start the Application ---
ui.run(
    title='Secure Password Suite', 
    favicon='🔑',
    storage_secret='my-super-secret-key-that-is-long',
    port=8081
)