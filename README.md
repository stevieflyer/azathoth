# Azathoth

The development kit that gives birth to most of the Autom itself.

## Schema Converter

Schema Converter watch `autom-backend` and `autom`, extract all schema defintions and transform them into frontend typescript type declaration in `types/` directories.

## API Converter

API Converter watch `autom-backend` apis, convert it to `autom-frontend` api calls(at `/lib/backend-api/`) and server actions(at `app/_actions/`)
