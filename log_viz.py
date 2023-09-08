import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Visualisierung der Logdaten
# Erstelle Boxplots für alle Evaluationsmetriken unterteilt nach Prompt-Version
# muss geändert werden, wenn logstruktur geändert wird

def plot_bar_chart(ax, df, column, title):
    df = df[df['type'] == column]
    if df.empty:
        return
    sns.boxplot(x=df['try'], y=df['value'], ax=ax, width=0.5)
    ax.set_title(title)
    ax.set_xlabel('Prompt-Version')

# Read the CSV data into a dataframe
csv_file = 'logs/allinone.csv' 
df = pd.read_csv(csv_file, sep=';', header=None, names=['level', 'timestamp', 'log', 'try', 'user_id', 'type', 'value'])

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10))

print(df['value'])
df['value'] = df['value'].apply(lambda x: 1 if x == 'increment' else (-1 if x == 'decrement' else x))
print(df['value'])
df['value'] = df['value'].astype(float)

plot_bar_chart(ax1, df, 'TOKENS', 'TOKENS')
plot_bar_chart(ax2, df, 'TIME', 'TIME')
plot_bar_chart(ax3, df, 'FeedbackType.RELEVANCE', 'FEEDBACK')

fig.suptitle('Boxplots for TOKENS, TIME, FEEDBACK')

plt.tight_layout()
plt.show()