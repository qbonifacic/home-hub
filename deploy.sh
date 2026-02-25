#!/bin/bash
set -e
git push origin main
echo "Triggering Render deploy..."
curl -s -X POST "https://api.render.com/v1/services/srv-d6f8ses50q8c73e25ip0/deploys" \
  -H "Authorization: Bearer rnd_qxNgP2OlanNWcJomIJnSM6kD88AP" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":"do_not_clear"}' > /dev/null
echo "✅ Deploy triggered — live in ~2 min"
