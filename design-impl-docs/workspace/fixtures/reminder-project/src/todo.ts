export type Todo = {
  id: string;
  title: string;
  done: boolean;
};

const todos: Todo[] = [];

export function addTodo(title: string): Todo {
  const todo: Todo = { id: crypto.randomUUID(), title, done: false };
  todos.push(todo);
  return todo;
}

export function completeTodo(id: string): void {
  const todo = todos.find((t) => t.id === id);
  if (todo) {
    todo.done = true;
  }
}

export function listTodos(): Todo[] {
  return [...todos];
}
