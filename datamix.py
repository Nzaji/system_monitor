import pandas as pd

# Charger le dataset
df = pd.read_excel("good_dataset.xlsx")

# Mélanger les lignes du dataset
df_shuffled = df.sample(frac=1).reset_index(drop=True)

# Sauvegarder le dataset mélangé
df_shuffled.to_excel("augmented_dataset_shuffled.xlsx", index=False)

print("Dataset mélangé avec succès et sauvegardé sous 'augmented_dataset_shuffled.xlsx'.")