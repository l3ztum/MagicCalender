from magic_calender import MagicCalender
from datetime import date


def main():
    """Draws a calender png based on the config and google calender api.
    """
    try:
        cal = MagicCalender(firstweekday=0)
        cal.load()
        cal.draw()
        cal.save(f"{date.today().isoformat()}.png")
    except RuntimeError as exc:
        print(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
