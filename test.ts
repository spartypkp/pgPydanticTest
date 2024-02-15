import { sql } from '@pgtyped-pydantic/runtime';

// Welcome to the worst hack of all time

const selectNodes =sql`
SELECT * FROM template_node`;

