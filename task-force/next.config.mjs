/** @type {import('next').NextConfig} */
import path from 'path';
import withPlugins from 'next-compose-plugins';
import withTM from 'next-transpile-modules';
import moduleAlias from 'module-alias';

moduleAlias.addAlias('@', path.resolve('src'));

/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { defaultLoaders }) => {
    config.resolve.alias['@'] = path.resolve('src');
    return config;
  },
};

export default withPlugins([withTM(['module-alias'])], nextConfig);
