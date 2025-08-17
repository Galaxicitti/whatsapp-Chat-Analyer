from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import seaborn as sns
import preprocessor, helper
import base64
from io import BytesIO

app = Flask(__name__)

# convert matplotlib figure to base64 string
def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)
    return img_base64


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files["chatfile"]
        if uploaded_file:
            data = uploaded_file.read().decode("utf-8")
            df = preprocessor.preprocess(data)

            # user list
            user_list = df['user'].unique().tolist()
            if 'group_notification' in user_list:
                user_list.remove('group_notification')
            user_list.sort()
            user_list.insert(0, "Overall")

            selected_user = request.form.get("selected_user", "Overall")
            if selected_user != "Overall":
                df = df[df['user'] == selected_user]


            # fetch stats
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

            # plots dict
            plots = {}

            # monthly timeline
            timeline = helper.monthly_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['message'], color='green')
            plt.xticks(rotation='vertical')
            plots["monthly_timeline"] = fig_to_base64(fig)

            # daily timeline
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
            plt.xticks(rotation='vertical')
            plots["daily_timeline"] = fig_to_base64(fig)

            # busy day
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation='vertical')
            plots["busy_day"] = fig_to_base64(fig)

            # busy month
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            plots["busy_month"] = fig_to_base64(fig)

            # heatmap
            user_heatmap = helper.activity_heatmap(selected_user, df)
            fig, ax = plt.subplots()
            sns.heatmap(user_heatmap, ax=ax)
            plots["heatmap"] = fig_to_base64(fig)

            most_busy_user_plot = None
            if selected_user == "Overall":
                top_users = df["user"].value_counts().head(5)

                fig, ax = plt.subplots()
                top_users.plot(kind="bar", ax=ax, color="skyblue")
                ax.set_title("Most Busy Users")
                ax.set_ylabel("Message Count")
                plt.xticks(rotation=45)
                most_busy_user_plot = fig_to_base64(fig)

            df_wc = helper.create_wordcloud(selected_user, df)
            fig, ax = plt.subplots()
            ax.imshow(df_wc)
            ax.axis("off")
            plots["wordcloud"] = fig_to_base64(fig)

            most_common_df = helper.most_common_words(selected_user, df)
            fig, ax = plt.subplots()
            ax.barh(most_common_df[0], most_common_df[1])
            plt.xticks(rotation='vertical')
            plots["common_words"] = fig_to_base64(fig)

            emoji_df = helper.emoji_helper(selected_user, df)
            fig, ax = plt.subplots()
            ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(), autopct="%0.2f")
            plots["emoji_pie"] = fig_to_base64(fig)
             



            return render_template(
                "analysis.html",
                num_messages=num_messages,
                words=words,
                num_media_messages=num_media_messages,
                num_links=num_links,
                plots=plots,
                user_list=user_list,
                selected_user=selected_user,
                most_busy_user_plot=most_busy_user_plot)

            

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
