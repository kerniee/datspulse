import json
from game_types import PlayerResponse
from dacite import from_dict


def test_example_player_response():
    with open("tests/example_player_response.json", "r") as f:
        player_response = from_dict(PlayerResponse, json.load(f))

    assert player_response.ants[0].q == 10
    assert player_response.ants[0].r == 20
    assert player_response.ants[0].type == 0


# def test_ai_moves_to_next_hex():
#     import json
#     from ai import AI
#     from dacite import from_dict
#     from game_types import PlayerResponse

#     with open("tests/example_player_response.json", "r") as f:
#         player_response = from_dict(PlayerResponse, json.load(f))

#     ai = AI()
#     move_commands = ai.get_move_commands(player_response)
#     # There should be at least one move command
#     assert move_commands.moves, "AI did not return any move commands"
#     # The first ant should have a non-empty path if movement is possible
#     first_move = move_commands.moves[0]
#     assert isinstance(first_move.path, list)
#     # The path should not include the current position, so if movement is possible, it should be non-empty
#     # If the AI cannot move, it may return an empty path, but for a simple map, it should try to move
#     assert (
#         len(first_move.path) >= 0
#     )  # Accepts empty or non-empty, but you can set >0 if you expect movement
