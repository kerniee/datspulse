import json
import os
import pickle
import time
from dataclasses import asdict

from dotenv import load_dotenv

from ai import AI
from client import DatsClient
from visualize_player_response_pygame import Visualizer


def main():
    load_dotenv(".env")
    client = DatsClient(api_token=os.environ["DATS_API_TOKEN"], production=True)

    # plt.ion()  # Enable interactive mode
    # fig, ax = plt.subplots(figsize=(10, 10))

    while True:
        try:
            registration = client.register()
        except Exception as e:
            if "you are too late" in str(e):
                print(e)
                time.sleep(10)
                continue
            else:
                raise e
        print(registration)

        if registration.lobbyEndsIn > 0:
            print(f"Waiting for lobby to end in {registration.lobbyEndsIn} seconds")
            time_to_sleep = min(registration.lobbyEndsIn + 1, 10)
            time.sleep(time_to_sleep)
        else:
            break

    cache_path = f"ai_ignore/{registration.realm}@main.py.pickle"
    ai = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                ai = pickle.load(f)
            print(f"Restored AI state from {cache_path}")
        except Exception as e:
            print(f"Failed to load AI state: {e}")
    if ai is None:
        ai = AI()
    visualizer = Visualizer()

    try:
        while visualizer.running:
            # print(client.logs())
            player_response = client.arena()
            with open(
                f"ai_ignore/player_response_{registration.realm}.json", "a+"
            ) as f:
                json.dump(asdict(player_response), f)
                f.write("\n\n\n")

            next_turn_in = player_response.nextTurnIn
            start_time = time.time()

            start_time = time.time()
            move_commands = ai.get_move_commands(player_response)
            end_time = time.time()
            print(f"Time taken to get move commands: {end_time - start_time} seconds")
            if move_commands:
                # print(f"Moving with commands: {move_commands}")
                client.move(move_commands)

            while time.time() < start_time + next_turn_in:
                if not visualizer.update(
                    player_response,
                    seen_tiles=ai.seen_tiles,
                    move_commands=move_commands,
                    remembered_enemies=list(ai.memory.get_enemy_hexes()),
                    remembered_food=list(ai.memory.get_food_hexes()),
                ):
                    break

            # plt.draw()
            # plt.pause(player_response.nextTurnIn)

            print()
    except KeyboardInterrupt:
        print("Interrupted by user. Saving AI state...")
    finally:
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(ai, f)
            print(f"AI state saved to {cache_path}")
        except Exception as e:
            print(f"Failed to save AI state: {e}")
        visualizer.close()


if __name__ == "__main__":
    main()
