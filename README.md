# Suslikmetr
GopherMeter is a virtual pet game where users raise, feed, and battle virtual gophers (similar to "sushliki" in Russian).  This README outlines the core functionality and commands of the GopherMeter bot.

## Getting Started

* /start: Initiate the game.  Optional referral links can be included for bonus rewards.  This command creates a user's gopher.
* Referral Links: Using a referral link during registration grants bonus rewards for both the referrer and the new user.


## Gopher Care and Feeding

* /treat: Feeds your gopher.  A cooldown period (approximately 3-4 hours) exists between feedings to prevent overfeeding.
* /bonus:  Provides bonus nuts (with a cooldown period).
* /searchnuts:  Attempts to find nuts (1% chance of success).
* /iron:  Pet your gopher to reset the feeding timer (once every 24 hours).
* /profile: Displays user ID, nut count, battle statistics, referral link, and avatar.
* /profile_test:  Provides a simplified version of /profile with basic breed information.


## Interaction and Social Features

* /tops:  Displays leaderboards for various categories (users, chats, groups).
* /lol:  Activates a (currently buggy) neural network; responds to bot messages.
* /give:  Transfers nuts to another player.
* /name:  Allows renaming of the gopher (maximum 25 characters).


## Shop and Inventory

* /store: Accesses the in-game store for useful items.
* /shop: Accesses the avatar shop (including NFT avatars).
* /buy: Purchases items from the store.
* /use: Uses a purchased item.
* /inventory:  Displays the user's inventory.


## Battles and Other Features

* /bite: (Currently under development) Initiates gopher battles.
* /setpromo [name] [amount] [time (hours)] [uses]:  Creates a promo code (admin only).
* /promo:  Redeems a promo code.
* /invest: Invests nuts into a group treasury (maximum 15 nuts per day).
* /withdraw: Withdraws nuts from a group treasury (maximum 15 nuts per day).
* /w:  Manages nut withdrawals (admin only).


## Future Updates

Future development includes:

* Premium subscription
* Clans
* Ban system
* Auction house
* Hunger mechanic (more sophisticated than the current feeding system)
* And more!


## Contributing

Contributions are welcome! Please see the news (https://t.me/suslik_master_gamebot_channel) file for details.

## License

[PROGVM TG: @pahabobyr @mcpeorakul]
