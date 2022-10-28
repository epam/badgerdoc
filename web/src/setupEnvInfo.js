const { writeFile } = require('fs');
const { exec } = require('child_process');

exec('git rev-parse --verify --short HEAD', (err, stdout, stderr) => {
    if (err) {
        console.error(err);
        throw err;
    }
    writeFile('./src/env-info.json', JSON.stringify({ lastCommitHash: stdout }), (err) => {
        if (err) {
            console.error(err);
            throw err;
        }
    });
});
