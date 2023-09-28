// temporary_disabled_rules
/* eslint-disable eqeqeq */
const isMocksAllowed = String(process.env.REACT_APP_ALLOW_MOCKS).toLocaleLowerCase() == 'true';

module.exports = function (req, res, next) {
    if (isMocksAllowed && req.url.includes('download')) {
        res.download(`${__dirname}/1.pdf`);
    } else {
        next();
    }
};
