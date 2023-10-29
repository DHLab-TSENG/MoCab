const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
    transpileDependencies: true,
    chainWebpack: config => {
        config
            .module
            .rule('csv')
            .test(/\.csv$/)
            .use('csv-loader')
            .loader('csv-loader')
            .options({
              dynamicTyping: true,
              header: true,
              skipEmptyLines: true
            })
            .end()
    },
    pages: {
        index: {
            entry: 'src/main.js',  // page 的入口
            template: 'public/index.html', // 模板来源
            filename: 'index.html', //  在 dist/index.html 的输出
        },
        launch: {
            entry: 'src/pages/launch/main.js',
            template: 'public/launch.html',
            filename: 'launch.html',
        },
    }
})
