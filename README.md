# Honeypot Cog for Red Bot

A lightweight moderation cog that lets you mark a single channel per guild as a honeypot. Anyone who sends a message in that channel has the message deleted and their account banned automatically, along with up to a day of message history removed via Discord's native ban cleanup.

## Features

- Configure a honeypot channel per guild with a simple admin command.
- Automatically deletes the triggering message in the honeypot channel.
- Bans the offender and prunes up to one day of message history through Discord's ban endpoint.
- Optional exemption list so trusted roles can speak in the honeypot without punishment.
- Fail-safe handling so missing permissions never crash your bot.

## Installation

### Using Red's Downloader (recommended)

```text
[p]repo add neufox-honeypot https://github.com/itsneufox/neufox-honeypot-cog
[p]cog install neufox-honeypot honeypot
[p]load honeypot
```

### Manual installation

1. Download or clone this repository.
2. Copy the `honeypot` folder into your Red bot's `cogs` directory.
3. Install requirements: `pip install -r requirements.txt`.
4. Load with `[p]load honeypot`.

## Configuration

Grant your bot `Manage Messages` in the honeypot channel and `Ban Members` server-wide. Then select the honeypot channel:

```text
[p]honeypot #trap-channel
```

You can re-run the command at any time to move the trap to another text channel.

## Usage

- `[p]honeypot <channel>` — Admin-only command that saves the honeypot channel for the guild.
- `[p]honeypotexempt` or `[p]honeypotexempt list` — Show roles currently exempt from the trap.
- `[p]honeypotexempt add <role>` — Add a role to the exempt list.
- `[p]honeypotexempt remove <role>` — Remove a role from the exempt list.
- Once configured, the cog watches all messages. If a non-exempt member speaks in the honeypot channel they are banned, their triggering message is deleted, and Discord automatically removes up to a day of their recent messages via `delete_message_days=1`.

## Permissions & Behavior

- The bot needs `Manage Messages` in the honeypot channel and `Ban Members` server-wide.
- Message cleanup relies on Discord's native ban option `delete_message_days=1`, which deletes up to 24 hours of the member's history.

## Troubleshooting

1. **Bot isn't deleting messages** — confirm it has `Manage Messages` in that channel.
2. **Bot isn't banning** — verify it has `Ban Members` and sits higher in the role hierarchy than the offender.
3. **Trusted members getting banned** — add their role to `[p]honeypotexempt add <role>`.
4. **Multiple honeypot channels?** — currently only one channel per guild can be configured; rerun `[p]honeypot` to change it.

## Contributing

Issues and pull requests are welcome. Please describe the scenario you are solving, include reproduction steps, and test your changes on a Red 3.5+ instance when possible.

## License

Released under the MIT License.
