from nicegui import ui
from functools import partial
from firebase_backend import add_task, update_task, delete_task, get_tasks
from datetime import datetime, timezone, time

# Add custom styles for an attractive UI
ui.add_head_html('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }

    .glass-card {
        background-color: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    }

    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.1);
    }

    .task-card {
        transition: all 0.2s ease-in-out;
    }
</style>
''')

@ui.page('/')
async def main():
    # --- State Management & Component References ---
    app_state = {'task_container': None, 'loading_spinner': None}
    search_input, sort_by_select, sort_direction_select = None, None, None

    # --- Core Logic Functions ---
    async def refresh_tasks():
        """Clears and reloads all tasks, applying current search and sort settings."""
        if not app_state['task_container']: return
        
        app_state['loading_spinner'].visible = True
        app_state['task_container'].clear()
        
        try:
            search_term = search_input.value.strip().lower() if search_input.value else ''
            all_tasks = get_tasks()
            
            filtered_tasks = [(t.id, t.to_dict()) for t in all_tasks if search_term in t.to_dict().get('text', '').lower()]
            
            sort_by = sort_by_select.value
            direction = sort_direction_select.value
            is_reversed = (direction == 'desc')

            if sort_by == 'Alphabetical':
                sort_key = lambda item: item[1].get('text', '').lower()
            elif sort_by == 'Due Date':
                sort_key = lambda item: item[1].get('due_date') or datetime.max.replace(tzinfo=timezone.utc)
            else: # Default to 'Creation Date'
                sort_key = lambda item: item[1].get('created_at') or datetime.min.replace(tzinfo=timezone.utc)

            filtered_tasks.sort(key=sort_key, reverse=is_reversed)
            
            with app_state['task_container']:
                if not filtered_tasks:
                    ui.label('No tasks found.').classes('text-gray-500 text-center py-8')
                else:
                    for task_id, task_data in filtered_tasks:
                        display_task(task_id, task_data)
        except Exception as e:
            ui.notify(f'Error loading tasks: {e}', color='negative')
            print(f"Error in refresh_tasks: {e}")
        finally:
            app_state['loading_spinner'].visible = False

    def display_task(task_id: str, task_data: dict):
        """Renders a single task card in the UI."""
        text, completed = task_data.get('text', ''), task_data.get('completed', False)
        current_status = 'Completed' if completed else 'Pending'
        due_date = task_data.get('due_date')
        
        with app_state['task_container']:
            with ui.card().classes('w-full task-card').props('flat bordered'):
                with ui.row().classes('items-center justify-between w-full'):
                    label_class = 'line-through text-gray-500' if completed else ''
                    ui.label(text).classes(f'text-sm {label_class} flex-1')
                    
                    with ui.row().classes('items-center gap-2'):
                        if due_date:
                            is_overdue = not completed and due_date.astimezone() < datetime.now().astimezone()
                            color = 'text-red-500' if is_overdue else 'text-gray-500'
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('event', color='red-5' if is_overdue else 'gray-5').classes('text-sm')
                                ui.label(due_date.astimezone().strftime("%b %d, %I:%M %p")).classes(f'text-xs {color}')
                        
                        ui.select(options=['Pending', 'Completed'], value=current_status, on_change=lambda e: handle_status_change(task_id, e)).props('dense outlined').classes('w-32')
                        
                        with ui.button(icon='edit', on_click=lambda: show_edit_dialog(task_id, task_data)).props('flat round color=primary'): ui.tooltip('Edit Task')
                        with ui.button(icon='delete', on_click=lambda: show_delete_dialog(task_id, text)).props('flat round color=negative'): ui.tooltip('Delete Task')

    # --- Handlers that interact with the backend ---
    async def handle_status_change(task_id: str, event):
        try:
            update_task(task_id, {'completed': (event.value == 'Completed')})
            ui.notify('Task status updated', color='positive')
            await refresh_tasks()
        except Exception as e:
            ui.notify(f'Error updating task: {e}', color='negative')

    def show_edit_dialog(task_id: str, task_data: dict):
        with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
            ui.label('Edit Task').classes('text-lg font-bold mb-4')
            edit_text = ui.input(label='Task text', value=task_data.get('text', '')).classes('w-full')
            
            current_due = task_data.get('due_date')
            initial_date = current_due.astimezone().strftime('%Y-%m-%d') if current_due else None
            initial_time = current_due.astimezone().strftime('%H:%M') if current_due else None

            with ui.row().classes('w-full items-center gap-2'):
                with ui.input('Due Date', value=initial_date).classes('flex-grow') as edit_date:
                    with ui.menu(): ui.date().bind_value(edit_date)
                with ui.input('Time', value=initial_time).classes('flex-grow') as edit_time:
                    with ui.menu(): ui.time().bind_value(edit_time)

            async def save_edit():
                if not all([edit_text.value.strip(), edit_date.value, edit_time.value]):
                    ui.notify('All fields are required.', color='negative'); return

                date_part = datetime.strptime(edit_date.value, '%Y-%m-%d').date()
                time_part = time.fromisoformat(edit_time.value)
                new_due = datetime.combine(date_part, time_part).astimezone()

                if new_due < datetime.now().astimezone():
                    ui.notify('Due date cannot be in the past.', color='negative'); return

                try:
                    update_task(task_id, {'text': edit_text.value.strip(), 'due_date': new_due})
                    ui.notify('Task updated successfully', color='positive')
                    await refresh_tasks()
                    dialog.close()
                except Exception as e:
                    ui.notify(f'Error updating task: {e}', color='negative')

            with ui.row().classes('gap-2 mt-4'):
                ui.button('Save', on_click=save_edit); ui.button('Cancel', on_click=dialog.close)
        dialog.open()

    async def show_delete_dialog(task_id: str, text: str):
        with ui.dialog() as dialog, ui.card():
            ui.label(f'Delete Task: "{text}"?').classes('text-lg font-bold')
            with ui.row().classes('gap-2 mt-4'):
                async def delete_confirmed():
                    try:
                        delete_task(task_id)
                        ui.notify('🗑️ Task deleted', color='warning')
                        await refresh_tasks()
                    except Exception as e:
                        ui.notify(f'Error deleting task: {e}', color='negative')
                    finally:
                        dialog.close()
                ui.button('Delete', on_click=delete_confirmed, color='red'); ui.button('Cancel', on_click=dialog.close)
        await dialog

    # --- UI LAYOUT ---
    with ui.column().classes('items-center w-full min-h-screen p-4 sm:p-8'):
        with ui.card().classes('glass-card max-w-2xl w-full p-6 sm:p-8 rounded-2xl'):
            ui.label('📝 My To-Do List').classes('text-4xl font-bold mb-6 text-center text-gray-800')

            # --- ADD TASK SECTION ---
            with ui.column().classes('w-full gap-2'):
                new_task_input = ui.input(placeholder='What needs to be done?').props('outlined dense').classes('w-full')
                with ui.row().classes('w-full items-center gap-2'):
                    due_date_input = ui.input('Due Date').props('dense outlined').classes('flex-grow')
                    with due_date_input.add_slot('append'):
                        ui.icon('event', color='primary').classes('cursor-pointer').on('click', lambda: menu_date.open())
                    with ui.menu() as menu_date: ui.date().bind_value(due_date_input)
                    
                    due_time_input = ui.input('Time').props('dense outlined').classes('flex-grow')
                    with due_time_input.add_slot('append'):
                        ui.icon('schedule', color='primary').classes('cursor-pointer').on('click', lambda: menu_time.open())
                    with ui.menu() as menu_time: ui.time().bind_value(due_time_input)
                
                async def handle_add_task():
                    if not all([new_task_input.value, new_task_input.value.strip(), due_date_input.value, due_time_input.value]):
                        ui.notify('Task, due date, and time are all required.', color='negative'); return

                    date_part = datetime.strptime(due_date_input.value, '%Y-%m-%d').date()
                    time_part = time.fromisoformat(due_time_input.value)
                    due_datetime = datetime.combine(date_part, time_part).astimezone()

                    if due_datetime < datetime.now().astimezone():
                        ui.notify('Due date cannot be in the past.', color='negative'); return

                    try:
                        add_task(new_task_input.value.strip(), due_date=due_datetime)
                        ui.notify('Task added successfully', color='positive')
                        new_task_input.value, due_date_input.value, due_time_input.value = '', None, None
                        await refresh_tasks()
                    except Exception as e:
                        ui.notify(f'Error adding task: {e}', color='negative')

                add_button = ui.button('Add Task', on_click=handle_add_task).props('color=primary rounded-lg w-full')

            ui.separator().classes('my-4')

            # --- SEARCH AND SORT SECTION ---
            with ui.column().classes('w-full gap-2'):
                # REQUIREMENT: Search on type by adding on_change event
                search_input = ui.input(
                    placeholder='Search tasks...'
                ).props('outlined dense clearable').classes('w-full').on('update:model-value', refresh_tasks)

                with ui.row().classes('w-full items-center gap-2'):
                    sort_by_select = ui.select(
                        options=['Creation Date', 'Due Date', 'Alphabetical'], 
                        value='Creation Date', label='Sort by'
                    ).props('dense outlined').classes('flex-grow')
                    
                    sort_direction_select = ui.select(
                        options={'desc': 'Descending', 'asc': 'Ascending'}, 
                        value='desc', label='Direction'
                    ).props('dense outlined').classes('flex-grow')

                    ui.button('Apply Sort', on_click=refresh_tasks).props('color=primary h-[40px]')
            
            # --- Task Display Area ---
            app_state['loading_spinner'] = ui.spinner(size='lg', color='primary').classes('my-4 self-center')
            app_state['task_container'] = ui.column().classes('w-full gap-3')

    # Initial load of tasks after the UI is built
    await refresh_tasks()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8081, reload=True, title="To-Do App")