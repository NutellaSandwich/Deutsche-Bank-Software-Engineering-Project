import numpy as np

def calculate_weights_from_matrix(matrix):
#     Calculates list of normalised weights from the AHP matrix given.
#     Parameters:
#         matrix - 2D array of floats produced through the AHP survey.
#     Returns:
#         weights - Normalised list of floats.
    
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = np.argmax(eigenvalues)
    priority_vector = eigenvectors[:, max_index]
    weights = priority_vector.real / np.sum(priority_vector.real)
    return weights
