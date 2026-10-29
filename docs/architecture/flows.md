# Flows

## Player login and join

![Player login sequence](../assets/diagrams/player-login.light.png#only-light)
![Player login sequence](../assets/diagrams/player-login.dark.png#only-dark)

The launcher signs in with Microsoft (Xbox Live → Minecraft services), syncs the modpack,
starts the game, and the player connects through Velocity, which forwards identity to the
server. The mod then loads the player's progression from the website API.

## Vote and reward

![Vote and reward sequence](../assets/diagrams/vote-and-reward.light.png#only-light)
![Vote and reward sequence](../assets/diagrams/vote-and-reward.dark.png#only-dark)

A voting site sends a NuVotifier vote to the proxy; the plugin gets a service token and posts
the vote to the website, which credits points and queues a reward. In game, the player claims
pending rewards; today the mod reads them straight from Postgres (an API is proposed).
