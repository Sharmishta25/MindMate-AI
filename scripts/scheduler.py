"""Run explicitly: python -m scripts.scheduler --once (or --loop)."""
import argparse,time
from mindmate.config import load_settings
from mindmate.database import initialize_database
from mindmate.services.scheduling import run_once


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loop',action='store_true'); parser.add_argument('--once',action='store_true')
    args=parser.parse_args(); settings=load_settings()
    from mindmate.security.crypto import Cipher
    Cipher(settings.encryption_keys)
    initialize_database(settings.database_path)
    while True:
        try:
            count=run_once(settings.database_path,settings.encryption_keys)
            print(f'Worker poll completed; delivered={count}. No external notifications are sent.')
        except Exception:
            print('Worker poll failed. Check key/storage configuration; no private error payload logged.')
            if not args.loop: raise SystemExit(1)
        if not args.loop: break
        time.sleep(60)


if __name__=='__main__': main()
