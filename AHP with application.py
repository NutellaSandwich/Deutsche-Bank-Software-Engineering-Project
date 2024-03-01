import tkinter as tk
import numpy as np

def update_matrix(matrix, i, j, value):
    matrix[i][j] = value
    matrix[j][i] = 1/value
    label.pack_forget()
    btn_1.pack_forget()
    btn_2.pack_forget()
    btn_3.pack_forget()
    show_next_choice()


def show_next_choice():
    global i, j
    i, j = np.where(matrix == 0)
    if i.size == 0:
        calculate_weights()
        return
    i = i[0]
    j = j[0]
    if i == j:
        matrix[i][j] = 1
        show_next_choice()
        return
    label.config(text=f"Which is more important: {criteria[i]} or {criteria[j]}?")
    btn_1.config(text=f"Equally important")
    btn_2.config(text=f"{criteria[i]} is more important")
    btn_3.config(text=f"{criteria[j]} is more important")
    label.pack()
    btn_1.pack()
    btn_2.pack()
    btn_3.pack()

def calculate_weights():
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = np.argmax(eigenvalues)
    priority_vector = eigenvectors[:, max_index]
    weights = priority_vector.real / np.sum(priority_vector.real)
    result = dict(zip(criteria, weights))
    label.config(text=f"Weights: \n" + "\n".join([f"{k}: {v:.2f}" for k, v in result.items()]))
    label.pack()

def main():
    global root, label, btn_1, btn_2, btn_3, criteria, matrix, i, j
    criteria = ['Budget', 'Team Size', 'Duration', 'A', 'B', 'C',"D","E","F","G"]
    matrix = np.zeros((len(criteria), len(criteria)))
    root = tk.Tk()
    root.title("AHP")
    root.config(bg='#80c1ff')

    label = tk.Label(root, text="", font=('Wing-Dings', 20), bg='#80c1ff', fg='#000000')
    label.pack(pady=20)

    btn_1 = tk.Button(root, text="", font=('Wing-Dings', 16), bg='#FFFFFF', fg='#000000',
                      command=lambda: update_matrix(matrix, i, j, 1), height=2, width=20)
    btn_1.pack(pady=10)

    btn_2 = tk.Button(root, text="", font=('Wing-Dings', 16), bg='#FFFFFF', fg='#000000',
                      command=lambda: update_matrix(matrix, i, j, 3), height=2, width=20)
    btn_2.pack(pady=10)

    btn_3 = tk.Button(root, text="", font=('Wing-Dings', 16), bg='#FFFFFF', fg='#000000',
                      command=lambda: update_matrix(matrix, i, j, 1/3), height=2, width=20)
    btn_3.pack(pady=10)

    show_next_choice()
    root.mainloop()

if __name__ == '__main__':
    main()