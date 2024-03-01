from db_schema import db, AHPWeights
import sqlite3
import json


def calculate_success_chance(factors, weightings):
#     Calculate the percentage chance of success based on the weightings and current values of factors.

#     :param factors: A list of floats representing the current values of factors.
#     :param weightings: A list of floats representing the weightings of the factors.
#     :return: A float representing the percentage chance of success.
    if None in factors:
         return None
        
        
    factor_ranges = [(1.0,5.0), (1.0,5.0), (-5.0, 5.0), (0.0, 168.0), (0.0, 1.0), (1.0, 5.0)]

    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    qry = json.loads(conn.execute("SELECT ahp_weights.weightings FROM ahp_weights LIMIT 1").fetchone()[0])
    indexes = [1, 2, 3, 6, 7, 9]
    weightings = [float(qry[x]) for x in indexes]
#     print(qry)
#     print(weightings)
    # weightings = [0.1,0.2,0.2,0.1,0.1,0.3]
    cursor.close()
    conn.close()

#     print("Weightings: ")
#     print(qry)

    # Scale the factor values
    scaled_factors = []
    for i in range(len(factors)):
        factor_range = factor_ranges[i][1] - factor_ranges[i][0]
        if factor_range == 0:
            scaled_factor = 1.0
        elif factor_range < 0:
            raise ValueError("Invalid factor range: min value is greater than max value.")
        else:
            # If the factor is the sixth factor, where closer to 0 is better,
            # flip the value and scale it to the range [0, 1] accordingly.
            if i == 2:
                if factors[i] >= 0:
                    scaled_factor = 1 - ((factors[i] / (factor_ranges[i][1] / 2)) / 2)
                else:
                    scaled_factor = 1 - ((abs(factors[i]) / (abs(factor_ranges[i][0]) / 2)) / 2)
            # Otherwise, scale the value to the range [0, 1] as usual.
            else:
                scaled_factor = (factors[i] - factor_ranges[i][0]) / factor_range
        scaled_factors.append(scaled_factor)
        
    # Normalize the weightings
    total_weighting = sum(weightings)
    normalized_weightings = [weight / total_weighting for weight in weightings]

    # Calculate the weighted average of the scaled factors
    weighted_sum = sum([scaled_factors[i] * normalized_weightings[i] for i in range(len(factors))])
    weighted_average = weighted_sum

    # Convert the weighted average back to a percentage
    success_chance = round(weighted_average * 100, 2)

    return success_chance
